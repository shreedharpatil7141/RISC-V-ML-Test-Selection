function stage11_run(mode)
% Stage 11 MATLAB baselines on the frozen Stage 10 dataset.
arguments
    mode (1,1) string {mustBeMember(mode,["train","validate"])}
end
root=fileparts(fileparts(fileparts(mfilename('fullpath'))));
outDir=fullfile(root,'reports','stage11_matlab_ml');
if mode=="train", trainStage11(root,outDir); else, validateStage11(root,outDir); end
end

function trainStage11(root,outDir)
dataDir=fullfile(root,'reports','stage10_dataset');
sourceFiles={fullfile(root,'scripts','machine_learning','stage11_run.m'), ...
    fullfile(root,'scripts','machine_learning','run_stage11_matlab.bat'), ...
    fullfile(root,'scripts','machine_learning','validate_stage11_matlab.bat')};
if ~license('test','Statistics_Toolbox') || isempty(which('fitctree')) || ...
        isempty(which('fitcnb')) || isempty(which('TreeBagger'))
    error('Statistics and Machine Learning Toolbox with fitctree, fitcnb, and TreeBagger is required.');
end
if ~startsWith(string(version('-release')),"2025")
    error('This batch targets an installed MATLAB R2025 release; found %s.',version('-release'));
end
if ~isfolder(outDir), mkdir(outDir); end
[F,L,S,D,C,stage10Hashes]=loadAndCheckStage10(root,dataDir);
ids=string(F.test_id); [tf,loc]=ismember(ids,string(S.test_id));
if ~all(tf), error('Feature rows do not align with logical-test split assignments.'); end
splitByID=string(S.split(loc)); trainMask=splitByID=="train";
valMask=splitByID=="validation"; testMask=splitByID=="test";
trainIDs=ids(trainMask); valIDs=ids(valMask); testIDs=ids(testMask);
if sum(trainMask)~=196 || sum(valMask)~=46 || sum(testMask)~=40
    error('Frozen Stage 10 split must remain 196/46/40.');
end

% No test names, raw seeds, hashes, family/suite fields, labels, costs, outcomes, or provenance enter X.
featureColumns=["program_bytes","unique_byte_values"];
forbidden=["test_id","scenario","seed","seed_numeric","family","template_family", ...
    "seed_family","suite","image_sha256","coverage","runtime","cycles", ...
    "status","outcome","evidence","provenance"];
if any(ismember(featureColumns,forbidden)), error('Identity/post-execution predictor selected.'); end
numericRaw=[toNumeric(F.program_bytes),toNumeric(F.unique_byte_values)];
if any(~isfinite(numericRaw),'all'), error('Static feature values are missing or non-finite.'); end
config=string(F.configuration); configLevels=sort(unique(config(trainMask)));
configRaw=zeros(height(F),numel(configLevels));
for k=1:numel(configLevels), configRaw(:,k)=double(config==configLevels(k)); end
numericMean=mean(numericRaw(trainMask,:),1); numericScale=std(numericRaw(trainMask,:),0,1);
numericScale(numericScale==0)=1;
X=[(numericRaw-numericMean)./numericScale,configRaw];
featureNames=[featureColumns,"configuration="+configLevels'];
if any(~isfinite(X),'all'), error('Train-only preprocessing produced non-finite values.'); end
preprocess=struct('numeric_columns',featureColumns,'training_mean',numericMean, ...
    'training_scale',numericScale,'configuration_levels_from_training',configLevels, ...
    'design_columns',featureNames,'fit_scope',"train_only",'train_ids',trainIDs);

simulators=["xsim","verilator"]; binIDs=sort(unique(string(D.bin_id)));
baseSeed=11011; nTrees=10; forestLeaf=3; treeLeaf=5; lambda=1e-2; thresholdGrid=(0.10:0.05:0.90)';
targetN=0; coverageModels=struct('simulator',{},'bin_id',{},'candidate_models',{}, ...
    'selected_model',{},'calibration',{},'threshold',{},'status',{}, ...
    'train_ids',{},'validation_ids',{},'train_positive',{},'train_negative',{});
validationRows=struct([]); predictionRows=struct([]); metricRows=struct([]);
for si=1:numel(simulators)
    sim=simulators(si);
    for bi=1:numel(binIDs)
        targetN=targetN+1; bin=binIDs(bi);
        if mod(targetN,25)==1, fprintf('Stage 11 fitting target %d/%d: %s / %s\n',targetN,2*numel(binIDs),sim,bin); end
        q=string(L.simulator)==sim & string(L.bin_id)==bin; LT=L(q,:);
        [found,order]=ismember(ids,string(LT.test_id));
        if ~all(found) || numel(unique(string(LT.test_id)))~=numel(ids)
            error('Label alignment failed for %s / %s.',sim,bin);
        end
        LT=LT(order,:); app=toNumeric(LT.applicable); avail=toNumeric(LT.available);
        actual=toNumeric(LT.value); state=string(LT.state);
        observed=app==1 & avail==1 & isfinite(actual);
        if any(observed & ~ismember(state,["observed_zero","observed_hit"])) || ...
                any(observed & actual~=0 & actual~=1)
            error('Invalid observed target values for %s / %s.',sim,bin);
        end
        if all(state=="unsupported")
            predictionRows=appendSkippedPredictions(predictionRows,ids,splitByID,valMask|testMask, ...
                sim,bin,app,avail,state,actual,"unsupported_target");
            metricRows=appendStruct(metricRows,blankCoverageMetric(sim,bin,"unsupported_target"));
            continue;
        end
        itrain=find(trainMask & observed); ival=find(valMask & observed); itest=find(testMask & observed);
        yTrain=actual(itrain); yVal=actual(ival); yTest=actual(itest);
        if isempty(itrain)
            predictionRows=appendSkippedPredictions(predictionRows,ids,splitByID,valMask|testMask, ...
                sim,bin,app,avail,state,actual,"no_training_labels");
            metricRows=appendStruct(metricRows,blankCoverageMetric(sim,bin,"no_training_labels"));
            continue;
        end
        trainPositive=sum(yTrain==1); trainNegative=sum(yTrain==0); prevalence=mean(yTrain);
        if numel(unique(yTrain))<2
            candidates=constantCandidate(yTrain(1));
        else
            candidates=fitCandidates(X(itrain,:),yTrain,baseSeed+targetN,nTrees,forestLeaf,treeLeaf,lambda);
        end
        valP=cell(numel(candidates),1); valBrier=inf(numel(candidates),1); comp=struct([]);
        for mi=1:numel(candidates)
            if candidates(mi).type=="failed"
                comp=appendStruct(comp,comparisonRecord(sim,bin,candidates(mi).name,numel(yVal), ...
                    sum(yVal==1),sum(yVal==0),NaN,NaN,"fit_failed: "+candidates(mi).error));
                continue;
            end
            if isempty(ival)
                comp=appendStruct(comp,comparisonRecord(sim,bin,candidates(mi).name,0,0,0,NaN,NaN,"no_validation_labels"));
                continue;
            end
            p=predictCandidate(candidates(mi),X(ival,:)); valP{mi}=p;
            valBrier(mi)=mean((p-yVal).^2); bm=binaryMetrics(yVal,p,0.5);
            comp=appendStruct(comp,comparisonRecord(sim,bin,candidates(mi).name,numel(yVal), ...
                sum(yVal==1),sum(yVal==0),valBrier(mi),bm.accuracy,"fit"));
        end
        % Validation alone chooses the model, calibration, and decision threshold.
        if isempty(ival) || numel(unique(yVal))<2
            chosen=find(strcmp({candidates.name},"majority"),1);
            if isempty(chosen), chosen=1; end
            selectStatus="validation_single_class_or_empty_majority_fallback";
        else
            [~,chosen]=min(valBrier); selectStatus="selected_by_validation_brier";
        end
        if isempty(valP{chosen})
            if isempty(ival), chosenValP=[]; else, chosenValP=predictCandidate(candidates(chosen),X(ival,:)); end
        else, chosenValP=valP{chosen}; end
        calibration=struct('method',"identity",'intercept',0,'slope',1,'fit_scope',"none");
        if numel(yVal)>=10 && sum(yVal==1)>=5 && sum(yVal==0)>=5, calibration=fitPlatt(chosenValP,yVal); end
        calibratedVal=applyCalibration(chosenValP,calibration); threshold=0.5;
        if numel(unique(yVal))==2, threshold=chooseThreshold(yVal,calibratedVal,thresholdGrid); end
        selectedName=string(candidates(chosen).name);
        if ~isempty(comp)
            for mi=1:numel(comp), comp(mi).selected=double(mi==chosen); comp(mi).selection_rule=selectStatus; end
            validationRows=appendStructArray(validationRows,comp);
        end
        for ri=find(valMask|testMask)'
            raw=NaN; calibrated=NaN; pred=NaN; predStatus="fit";
            if app(ri)==1 && state(ri)~="unsupported" && state(ri)~="inapplicable"
                raw=predictCandidate(candidates(chosen),X(ri,:));
                calibrated=applyCalibration(raw,calibration); pred=double(calibrated>=threshold);
            else, predStatus="target_not_applicable_for_test"; end
            predictionRows=appendStruct(predictionRows,predictionRecord(ids(ri),sim,bin,splitByID(ri),app(ri),avail(ri), ...
                state(ri),actual(ri),selectedName,raw,calibrated,threshold,pred,predStatus));
        end
        % Test metrics occur only after the model/calibration/threshold are locked.
        if ~isempty(itest)
            rawTest=predictCandidate(candidates(chosen),X(itest,:)); pTest=applyCalibration(rawTest,calibration);
            mt=binaryMetrics(yTest,pTest,threshold);
            mb=binaryMetrics(yTest,double(prevalence>=0.5)*ones(size(yTest)),0.5);
        else, mt=binaryMetrics([],[],threshold); mb=binaryMetrics([],[],0.5); end
        metricRows=appendStruct(metricRows,coverageMetric(sim,bin,selectStatus,numel(itrain),trainPositive,trainNegative, ...
            numel(ival),sum(yVal==1),sum(yVal==0),numel(itest),sum(yTest==1),sum(yTest==0), ...
            mt,mb,trainPositive<5,selectedName,threshold,calibration.method));
        coverageModels(end+1)=struct('simulator',sim,'bin_id',bin,'candidate_models',candidates(chosen), ...
            'selected_model',selectedName,'calibration',calibration,'threshold',threshold, ...
            'status',selectStatus,'train_ids',ids(itrain),'validation_ids',ids(ival), ...
            'train_positive',trainPositive,'train_negative',trainNegative); %#ok<AGROW>
    end
end
[costModels,costPredRows,costMetricRows]=trainCycleCosts(X,ids,splitByID,C,simulators,baseSeed);
writeStructTable(fullfile(outDir,'validation_model_comparison.csv'),validationRows);
writeStructTable(fullfile(outDir,'predictions.csv'),predictionRows);
writeStructTable(fullfile(outDir,'metrics_per_bin.csv'),metricRows);
writeStructTable(fullfile(outDir,'metrics_aggregate.csv'),aggregateMetrics(metricRows,simulators));
writeStructTable(fullfile(outDir,'cycle_predictions.csv'),costPredRows);
writeStructTable(fullfile(outDir,'cycle_cost_metrics.csv'),costMetricRows);
tools=ver; toolboxNames=string({tools.Name}); toolboxVersions=string({tools.Version});
configDoc=struct('logical_tests',282,'independent_training_units',196, ...
    'split_sizes',struct('train',196,'validation',46,'test',40), ...
    'simulator_targets',simulators,'prediction_task',"per-simulator per-bin coverage from pre-execution features", ...
    'excluded_predictors',forbidden,'predictor_columns',featureNames, ...
    'preprocessing',"numeric mean/std fit on train IDs only; configuration levels learned from train only", ...
    'models',{{"majority","fitctree","fitcnb-normal","TreeBagger-10","custom-logistic-ridge"}}, ...
    'decision_tree_min_leaf',treeLeaf,'forest_trees',nTrees,'forest_min_leaf',forestLeaf, ...
    'logistic_lambda',lambda,'model_choice',"minimum validation Brier score", ...
    'calibration',"validation Platt sigmoid with >=5 positives and >=5 negatives; otherwise identity", ...
    'thresholds',thresholdGrid,'seed_scheme',"twister; base + sorted simulator/bin target index; fixed per-model offsets", ...
    'test_policy',"choices locked before test evaluation", ...
    'cost_task',"separate observed_cycles model per simulator; wall_seconds not modeled", ...
    'seed',baseSeed,'matlab_release',version('-release'),'matlab_version',version, ...
    'matlab_root',matlabroot,'statistics_toolbox_license',logical(license('test','Statistics_Toolbox')), ...
    'toolboxes',toolboxNames,'toolbox_versions',toolboxVersions, ...
    'limitations',"Exploratory small corpus; no generalization or superiority claim; simulator metrics not pooled.");
writeText(fullfile(outDir,'configuration.json'),jsonencode(configDoc,'PrettyPrint',true));
save(fullfile(outDir,'models.mat'),'coverageModels','costModels','preprocess','trainIDs','valIDs','testIDs','-v7.3');
loaded=load(fullfile(outDir,'models.mat'),'coverageModels','costModels','preprocess');
if numel(loaded.coverageModels)~=numel(coverageModels) || ~isequal(string(loaded.preprocess.train_ids),trainIDs)
    error('Serialized model bundle did not round-trip.');
end
writeText(fullfile(outDir,'validation_evidence.txt'),sprintf(['STAGE11 MATLAB VALIDATION PASS\nrelease=%s\n' ...
    'logical_tests=282\ntrain_validation_test=196,46,40\nsimulator_rows_not_pooled=true\n' ...
    'train_only_preprocessing=true\nserialization_roundtrip=PASS\ninput_hashes=PASS\n'],version('-release')));
inputHashes=stage10Hashes;
for k=1:numel(sourceFiles)
    rel=strrep(sourceFiles{k},[root filesep],''); inputHashes(end+1)=struct('path',strrep(rel,'\','/'),'sha256',sha256File(sourceFiles{k})); %#ok<AGROW>
end
listing=dir(fullfile(outDir,'*')); outputFiles=struct();
for k=1:numel(listing)
    if listing(k).isdir || strcmp(listing(k).name,'manifest.json'), continue; end
    p=fullfile(outDir,listing(k).name);
    outputFiles.(matlab.lang.makeValidName(listing(k).name))=struct('path',listing(k).name,'sha256',sha256File(p));
end
manifest=struct('schema_version',"stage11-matlab-ml-1.0.0", ...
    'base_commit',"2d195e581075c1a4cb7bb17d172d22a7472a8a9b", ...
    'approved_stage10_commit',"2d195e581075c1a4cb7bb17d172d22a7472a8a9b", ...
    'input_hashes',inputHashes,'output_files',outputFiles,'validation_status',"PASS", ...
    'logical_tests',282,'training_examples_per_simulator',196,'test_examples_per_simulator',40, ...
    'simulator_rows_pooled',false,'preprocessing_scope',"train_only",'generalization_claim',false);
writeText(fullfile(outDir,'manifest.json'),jsonencode(manifest,'PrettyPrint',true));
validateStage11(root,outDir);
end

function [F,L,S,D,C,hashes]=loadAndCheckStage10(root,dataDir)
manifestPath=fullfile(dataDir,'manifest.json'); text=fileread(manifestPath);
hashes=struct('path',"reports/stage10_dataset/manifest.json",'sha256',sha256File(manifestPath));
block=extractJsonBlock(text,'input_hashes'); pairs=regexp(block,'"([^"]+)"\s*:\s*"([0-9a-f]{64})"','tokens');
for k=1:numel(pairs)
    rel=pairs{k}{1}; p=resolveLineagePath(root,rel);
    if ~isfile(p) || ~strcmpi(sha256File(p),pairs{k}{2}), error('Stage 10 input hash mismatch: %s',rel); end
    hashes(end+1)=struct('path',rel,'sha256',pairs{k}{2}); %#ok<AGROW>
end
block=extractJsonBlock(text,'csv_outputs');
pairs=regexp(block,'"([^"]+\.csv)"\s*:\s*\{\s*"rows"\s*:\s*(\d+)\s*,\s*"sha256"\s*:\s*"([0-9a-f]{64})"','tokens');
for k=1:numel(pairs)
    rel=pairs{k}{1}; p=fullfile(dataDir,rel);
    % Stage 10 CSV hashes describe LF exports. Git's Windows checkout may
    % expand those line endings, so verify the canonical LF representation.
    if ~isfile(p) || ~strcmpi(sha256NormalizedTextFile(p),pairs{k}{3}), error('Stage 10 CSV hash mismatch: %s',rel); end
    hashes(end+1)=struct('path',["reports/stage10_dataset/"+rel],'sha256',pairs{k}{3}); %#ok<AGROW>
end
if numel(pairs)~=10 || ~contains(text,'"schema_version": "stage10-dataset-1.0.0"')
    error('Frozen Stage 10 manifest/schema changed.');
end
F=readtable(fullfile(dataDir,'features.csv'),'TextType','string','VariableNamingRule','preserve');
L=readtable(fullfile(dataDir,'coverage_labels.csv'),'TextType','string','VariableNamingRule','preserve');
S=readtable(fullfile(dataDir,'split_assignments.csv'),'TextType','string','VariableNamingRule','preserve');
D=readtable(fullfile(dataDir,'bin_dictionary.csv'),'TextType','string','VariableNamingRule','preserve');
C=readtable(fullfile(dataDir,'execution_costs.csv'),'TextType','string','VariableNamingRule','preserve');
ids=string(F.test_id); sids=string(S.test_id);
if height(F)~=282 || numel(unique(ids))~=282 || height(S)~=282 || numel(unique(sids))~=282 || ~isequal(ids,sids)
    error('Stage 10 feature/split logical IDs are invalid or misaligned.');
end
split=string(S.split);
if sum(split=="train")~=196 || sum(split=="validation")~=46 || sum(split=="test")~=40
    error('Frozen Stage 10 split changed from 196/46/40.');
end
group=string(S.group_id);
for g=unique(group)'
    if numel(unique(split(group==g)))~=1, error('Split leakage in group %s.',g); end
end
if height(C)~=564 || sum(string(C.simulator)=="xsim")~=282 || sum(string(C.simulator)=="verilator")~=282
    error('Expected 282 separate cost rows per simulator.');
end
if height(L)~=178224 || numel(unique(string(D.bin_id)))~=height(D), error('Coverage/dictionary row count or IDs invalid.'); end
labelKeys=string(L.test_id)+"|"+string(L.simulator)+"|"+string(L.bin_id);
if numel(unique(labelKeys))~=height(L) || ~isequal(sort(unique(string(L.bin_id))),sort(unique(string(D.bin_id))))
    error('Coverage label keys do not align to the frozen bin dictionary.');
end
app=toNumeric(L.applicable); avail=toNumeric(L.available); value=toNumeric(L.value); state=string(L.state);
if any(~ismember(app,[0 1])) || any(~ismember(avail,[0 1])) || ...
        any((state=="observed_zero") & (app~=1 | avail~=1 | value~=0)) || ...
        any((state=="observed_hit") & (app~=1 | avail~=1 | value~=1)) || ...
        any((state=="inapplicable" | state=="unsupported") & (app~=0 | avail~=0)) || ...
        any((state=="unavailable") & (app~=1 | avail~=0)) || ...
        any(~ismember(state,["observed_zero","observed_hit","inapplicable","unsupported","unavailable"]))
    error('Stage 10 masks/evidence states are invalid.');
end
end

function candidates=fitCandidates(X,y,seed,nTrees,forestLeaf,treeLeaf,lambda)
classes=categorical(string(y),["0","1"]); majority=constantCandidate(double(mean(y)>=0.5)); majority.name="majority";
candidates=majority;
try, rng(seed,'twister'); m=fitctree(X,classes,'MinLeafSize',treeLeaf,'SplitCriterion','gdi'); candidates(end+1)=candidate("decision_tree","fitctree",m,NaN,"");
catch e, candidates(end+1)=candidate("decision_tree","failed",[],NaN,string(e.message)); end
try, rng(seed+1,'twister'); m=fitcnb(X,classes,'DistributionNames','normal'); candidates(end+1)=candidate("naive_bayes","fitcnb",m,NaN,"");
catch e, candidates(end+1)=candidate("naive_bayes","failed",[],NaN,string(e.message)); end
try
    rng(seed+2,'twister'); m=TreeBagger(nTrees,X,classes,'Method','classification', ...
        'MinLeafSize',forestLeaf,'NumPredictorsToSample',max(1,round(sqrt(size(X,2)))),'OOBPrediction','off');
    candidates(end+1)=candidate("random_forest","TreeBagger",m,NaN,"");
catch e, candidates(end+1)=candidate("random_forest","failed",[],NaN,string(e.message)); end
try, candidates(end+1)=candidate("logistic_ridge","logistic",logisticRidge(X,y,lambda),NaN,"");
catch e, candidates(end+1)=candidate("logistic_ridge","failed",[],NaN,string(e.message)); end
end

function c=candidate(name,type,model,probability,err)
c=struct('name',string(name),'type',string(type),'model',model,'probability',double(probability),'error',string(err));
end
function c=constantCandidate(label), c=candidate("constant","constant",double(label),double(label),""); end
function p=predictCandidate(c,X)
switch c.type
    case "constant", p=repmat(c.probability,size(X,1),1);
    case {"fitctree","fitcnb","TreeBagger"}
        [~,scores]=predict(c.model,X); p=positiveScore(scores,string(c.model.ClassNames));
    case "logistic", p=sigmoid([ones(size(X,1),1),X]*c.model);
    otherwise, error('Cannot predict using model type %s.',c.type);
end
p=min(max(double(p(:)),1e-8),1-1e-8);
end
function p=positiveScore(scores,classes)
idx=find(string(classes(:))=="1",1); if isempty(idx), p=zeros(size(scores,1),1); else, p=scores(:,idx); end
end
function beta=logisticRidge(X,y,lambda)
A=[ones(size(X,1),1),X]; beta=zeros(size(A,2),1);
for it=1:80
    p=sigmoid(A*beta); w=max(p.*(1-p),1e-6); g=(A'*(p-y))/size(A,1);
    g(2:end)=g(2:end)+lambda*beta(2:end);
    H=(A'*(A.*w))/size(A,1)+lambda*diag([0;ones(size(A,2)-1,1)]);
    step=H\g; beta=beta-step; if norm(step)<1e-7, break; end
end
if any(~isfinite(beta)), error('Non-finite logistic coefficients.'); end
end

function c=fitPlatt(p,y)
p=min(max(p(:),1e-6),1-1e-6); z=log(p./(1-p)); A=[ones(numel(z),1),z]; b=[log(mean(y)/(1-mean(y)));1];
for it=1:60
    q=sigmoid(A*b); w=max(q.*(1-q),1e-6); g=A'*(q-y)+[0;1e-3*b(2)];
    H=A'*(A.*w)+diag([1e-6,1e-3]); step=H\g; b=b-step; if norm(step)<1e-7, break; end
end
c=struct('method',"validation_platt",'intercept',b(1),'slope',b(2),'fit_scope',"validation_only");
end
function p=applyCalibration(raw,c)
if isempty(raw), p=[]; return; end
raw=min(max(raw(:),1e-6),1-1e-6);
if string(c.method)=="validation_platt", z=log(raw./(1-raw)); p=sigmoid(c.intercept+c.slope*z); else, p=raw; end
end
function t=chooseThreshold(y,p,grid)
best=-Inf; t=0.5; distance=Inf;
for th=grid'
    m=binaryMetrics(y,p,th); d=abs(th-0.5);
    if isfinite(m.balanced_accuracy) && (m.balanced_accuracy>best+1e-12 || ...
            (abs(m.balanced_accuracy-best)<=1e-12 && d<distance))
        best=m.balanced_accuracy; t=th; distance=d;
    end
end
end
function m=binaryMetrics(y,p,t)
y=double(y(:)); p=double(p(:)); m=struct('accuracy',NaN,'balanced_accuracy',NaN,'precision',NaN, ...
    'recall',NaN,'f1',NaN,'auc',NaN,'brier',NaN);
if isempty(y), return; end
pred=double(p>=t); tp=sum(pred==1 & y==1); tn=sum(pred==0 & y==0); fp=sum(pred==1 & y==0); fn=sum(pred==0 & y==1);
m.accuracy=mean(pred==y); m.precision=tp/max(tp+fp,1); m.recall=tp/max(tp+fn,1);
m.f1=2*m.precision*m.recall/max(m.precision+m.recall,eps); m.brier=mean((p-y).^2);
if any(y==1) && any(y==0)
    m.balanced_accuracy=0.5*(tp/sum(y==1)+tn/sum(y==0)); pos=p(y==1); neg=p(y==0); wins=0;
    for i=1:numel(pos), wins=wins+sum(pos(i)>neg)+0.5*sum(pos(i)==neg); end
    m.auc=wins/(numel(pos)*numel(neg));
end
end

function rows=appendSkippedPredictions(rows,ids,splits,mask,sim,bin,app,avail,state,actual,status)
for i=find(mask)'
        rows=appendStruct(rows,predictionRecord(ids(i),sim,bin,splits(i),app(i),avail(i),state(i),actual(i), ...
        "",NaN,NaN,NaN,NaN,status));
end
end
function r=predictionRecord(id,sim,bin,split,app,avail,state,actual,model,raw,cal,threshold,pred,status)
r=struct('test_id',string(id),'simulator',string(sim),'bin_id',string(bin),'split',string(split), ...
    'applicable',double(app),'available',double(avail),'actual_state',string(state), ...
    'actual_value',double(actual),'selected_model',string(model),'raw_probability',double(raw), ...
    'calibrated_probability',double(cal),'threshold',double(threshold),'predicted_label',double(pred), ...
    'model_status',string(status));
end
function r=coverageMetric(sim,bin,status,ntr,posTr,negTr,nv,posV,negV,nt,posT,negT,mt,mb,rare,model,threshold,cal)
r=struct('simulator',string(sim),'bin_id',string(bin),'selection_status',string(status), ...
    'train_support',ntr,'train_positive',posTr,'train_negative',negTr, ...
    'validation_support',nv,'validation_positive',posV,'validation_negative',negV, ...
    'test_support',nt,'test_positive',posT,'test_negative',negT, ...
    'accuracy',mt.accuracy,'balanced_accuracy',mt.balanced_accuracy,'precision',mt.precision, ...
    'recall',mt.recall,'f1',mt.f1,'auc',mt.auc,'brier',mt.brier, ...
    'baseline_accuracy',mb.accuracy,'baseline_balanced_accuracy',mb.balanced_accuracy, ...
    'baseline_brier',mb.brier,'rare_positive',double(rare),'selected_model',string(model), ...
    'threshold',double(threshold),'calibration',string(cal));
end
function r=blankCoverageMetric(sim,bin,status)
m=binaryMetrics([],[],0.5); r=coverageMetric(sim,bin,status,0,0,0,0,0,0,0,0,0,m,m,false,"",NaN,"none");
end
function r=comparisonRecord(sim,bin,model,n,pos,neg,brier,accuracy,status)
r=struct('simulator',string(sim),'bin_id',string(bin),'model',string(model),'validation_n',n, ...
    'validation_positive',pos,'validation_negative',neg,'validation_brier',brier, ...
    'validation_accuracy_at_half',accuracy,'fit_status',string(status),'selected',0,'selection_rule',"");
end
function rows=aggregateMetrics(perBin,simulators)
rows=struct([]); names=["accuracy","balanced_accuracy","precision","recall","f1","auc","brier", ...
    "baseline_accuracy","baseline_balanced_accuracy","baseline_brier"];
for sim=simulators
    q=string({perBin.simulator})==sim & [perBin.test_support]>0;
    for name=names
        v=[perBin(q).(name)]; v=v(isfinite(v)); if isempty(v), macro=NaN; else, macro=mean(v); end
        rows=appendStruct(rows,struct('simulator',sim,'metric',name,'macro_test_value',macro, ...
            'bins_with_test_support',sum(q),'logical_tests_per_simulator',40,'simulator_rows_pooled',false));
    end
end
end

function [models,predRows,metricRows]=trainCycleCosts(X,ids,splitByID,C,simulators,seed)
models=struct('simulator',{},'selected_model',{},'model',{},'train_ids',{},'validation_ids',{});
predRows=struct([]); metricRows=struct([]);
for si=1:numel(simulators)
    sim=simulators(si); T=C(string(C.simulator)==sim,:); [tf,loc]=ismember(ids,string(T.test_id));
    if ~all(tf) || numel(unique(string(T.test_id)))~=numel(ids), error('Cycle identity alignment failed for %s.',sim); end
    T=T(loc,:); y=toNumeric(T.observed_cycles);
    if any(~isfinite(y)) || any(string(T.status)~="PASS") || any(string(T.cycles_unit)~="cycle")
        error('Cycle costs are incomplete/invalid for %s.',sim);
    end
    tr=splitByID=="train"; va=splitByID=="validation"; te=splitByID=="test";
    medianModel=struct('name',"median_baseline",'type',"median",'model',median(y(tr)),'error',"");
    ridge=struct('name',"ridge",'type',"ridge",'model',[],'error',"");
    try
        A=[ones(sum(tr),1),X(tr,:)]; P=diag([0;ones(size(X,2),1)]);
        ridge.model=(A'*A+P)\(A'*y(tr));
    catch e, ridge.type="failed"; ridge.error=string(e.message); end
    tree=struct('name',"regression_tree",'type',"tree",'model',[],'error',"");
    try, rng(seed+si,'twister'); tree.model=fitrtree(X(tr,:),y(tr),'MinLeafSize',5);
    catch e, tree.type="failed"; tree.error=string(e.message); end
    candidates=[medianModel,ridge,tree]; valMAE=inf(1,numel(candidates));
    for k=1:numel(candidates)
        if candidates(k).type~="failed", valMAE(k)=mean(abs(predictCost(candidates(k),X(va,:))-y(va))); end
    end
    [~,chosen]=min(valMAE); selected=candidates(chosen);
    valPred=predictCost(selected,X(va,:)); testPred=predictCost(selected,X(te,:));
    models(end+1)=struct('simulator',sim,'selected_model',selected.name,'model',selected, ...
        'train_ids',ids(tr),'validation_ids',ids(va)); %#ok<AGROW>
    vi=find(va); ti=find(te);
    for k=1:numel(vi)
        predRows=appendStruct(predRows,costPrediction(ids(vi(k)),sim,"validation",y(vi(k)),valPred(k),selected.name));
    end
    for k=1:numel(ti)
        predRows=appendStruct(predRows,costPrediction(ids(ti(k)),sim,"test",y(ti(k)),testPred(k),selected.name));
    end
    med=median(y(tr)); metricRows=appendStruct(metricRows,struct('simulator',sim,'target',"observed_cycles", ...
        'selected_model',selected.name,'train_n',sum(tr),'validation_n',sum(va),'test_n',sum(te), ...
        'test_mae',mean(abs(testPred-y(te))),'test_rmse',sqrt(mean((testPred-y(te)).^2)), ...
        'median_baseline_mae',mean(abs(med-y(te))),'median_baseline_rmse',sqrt(mean((med-y(te)).^2)), ...
        'test_r2',1-sum((testPred-y(te)).^2)/max(sum((y(te)-mean(y(te))).^2),eps), ...
        'unit',"cycle"));
end
end

function y=predictCost(c,X)
switch c.type
    case "median", y=repmat(c.model,size(X,1),1);
    case "ridge", y=[ones(size(X,1),1),X]*c.model;
    case "tree", y=predict(c.model,X);
    otherwise, error('Invalid cycle model type %s.',c.type);
end
end
function r=costPrediction(id,sim,split,actual,pred,model)
r=struct('test_id',string(id),'simulator',string(sim),'split',string(split), ...
    'target',"observed_cycles",'actual_cycles',double(actual),'predicted_cycles',double(pred), ...
    'unit',"cycle",'selected_model',string(model));
end

function validateStage11(root,outDir)
manifestPath=fullfile(outDir,'manifest.json');
if ~isfile(manifestPath), error('Stage 11 manifest missing; run training first.'); end
manifest=jsondecode(fileread(manifestPath));
if manifest.schema_version~="stage11-matlab-ml-1.0.0" || ...
        manifest.base_commit~="2d195e581075c1a4cb7bb17d172d22a7472a8a9b"
    error('Stage 11 lineage/schema does not match approved Stage 10.');
end
[F,L,S,D,C,~]=loadAndCheckStage10(root,fullfile(root,'reports','stage10_dataset')); %#ok<ASGLU>
for k=1:numel(manifest.input_hashes)
    rel=manifest.input_hashes(k).path; p=resolveLineagePath(root,rel);
    if startsWith(rel,'reports/stage10_dataset/') && endsWith(rel,'.csv')
        actualHash=sha256NormalizedTextFile(p);
    else
        actualHash=sha256File(p);
    end
    if ~isfile(p) || ~strcmpi(actualHash,manifest.input_hashes(k).sha256), error('Stage 11 input hash mismatch: %s',rel); end
end
outBlock=extractJsonBlock(fileread(manifestPath),'output_files');
outPairs=regexp(outBlock,'"path"\s*:\s*"([^"]+)"\s*,\s*"sha256"\s*:\s*"([0-9a-f]{64})"','tokens');
for k=1:numel(outPairs)
    p=fullfile(outDir,outPairs{k}{1});
    if ~isfile(p) || ~strcmpi(sha256File(p),outPairs{k}{2}), error('Stage 11 output hash mismatch: %s',outPairs{k}{1}); end
end
if numel(outPairs)<8, error('Stage 11 artifact lineage is incomplete.'); end
pred=readtable(fullfile(outDir,'predictions.csv'),'TextType','string','VariableNamingRule','preserve');
metrics=readtable(fullfile(outDir,'metrics_per_bin.csv'),'TextType','string','VariableNamingRule','preserve');
config=jsondecode(fileread(fullfile(outDir,'configuration.json')));
bundle=load(fullfile(outDir,'models.mat'),'coverageModels','costModels','preprocess');
trainIDs=string(S.test_id(string(S.split)=="train"));
if ~isequal(string(bundle.preprocess.train_ids),trainIDs) || bundle.preprocess.fit_scope~="train_only"
    error('Preprocessing was not fitted only on frozen training IDs.');
end
if any(string(pred.split)=="train") || any(~ismember(string(pred.split),["validation","test"]))
    error('Prediction export includes an invalid split.');
end
if numel(unique(string(pred.test_id)+"|"+string(pred.simulator)+"|"+string(pred.bin_id)+"|"+string(pred.split)))~=height(pred)
    error('Duplicate prediction identity.');
end
if any(~ismember(string(metrics.simulator),["xsim","verilator"])) || numel(bundle.costModels)~=2
    error('Simulator-specific models/cost artifacts are incomplete.');
end
if config.logical_tests~=282 || config.independent_training_units~=196 || ...
        config.split_sizes.validation~=46 || config.split_sizes.test~=40
    error('Stage 11 configuration does not preserve frozen sample counts.');
end
rawFeatures=[toNumeric(F.program_bytes),toNumeric(F.unique_byte_values)]; tr=string(S.split)=="train";
if any(abs(mean(rawFeatures(tr,:),1)-bundle.preprocess.training_mean)>1e-12) || ...
        any(abs(std(rawFeatures(tr,:),0,1)-bundle.preprocess.training_scale)>1e-12)
    error('Serialized preprocessing differs from training-only statistics.');
end
levels=sort(unique(string(F.configuration(tr))));
if ~isequal(levels(:),string(bundle.preprocess.configuration_levels_from_training(:)))
    error('Configuration encoding was not learned from training rows only.');
end
if ~isfile(fullfile(outDir,'validation_evidence.txt')) || ...
        ~contains(fileread(fullfile(outDir,'validation_evidence.txt')),'serialization_roundtrip=PASS')
    error('Validation evidence file is missing.');
end
% Re-score a held-out prediction from the serialized selected model.
rawP=toNumeric(pred.raw_probability); j=find(string(pred.split)=="test" & isfinite(rawP),1);
if isempty(j), error('No applicable held-out predictions to verify serialization.'); end
rec=find(string({bundle.coverageModels.simulator})==string(pred.simulator(j)) & ...
    string({bundle.coverageModels.bin_id})==string(pred.bin_id(j)),1);
if isempty(rec), error('Selected model artifact is missing for prediction.'); end
modelRec=bundle.coverageModels(rec); candidateIndex=find(arrayfun(@(c)c.name==modelRec.selected_model,modelRec.candidate_models),1);
if isempty(candidateIndex), error('Serialized selected classifier was not found.'); end
cfg=string(F.configuration); row=find(string(F.test_id)==string(pred.test_id(j)),1);
if isempty(row), error('Held-out prediction test ID is missing from Stage 10 features.'); end
cfgOne=double(cfg(row)==bundle.preprocess.configuration_levels_from_training');
Xone=[(rawFeatures(row,:)-bundle.preprocess.training_mean)./bundle.preprocess.training_scale,cfgOne];
replay=predictCandidate(modelRec.candidate_models(candidateIndex),Xone);
replay=applyCalibration(replay,modelRec.calibration);
if abs(replay-toNumeric(pred.calibrated_probability(j)))>1e-10, error('Serialized model prediction round-trip changed.'); end
if height(pred)~=86*316*2 || height(metrics)~=632, error('Stage 11 prediction/metric row alignment failed.'); end
fprintf('STAGE11 VALIDATION PASS release=%s predictions=%d per_bin_metrics=%d cycle_models=%d\n', ...
    version('-release'),height(pred),height(metrics),numel(bundle.costModels));
end

function block=extractJsonBlock(json,key)
pat=['"' key '"\s*:\s*\{']; [~,e]=regexp(json,pat,'start','end','once');
if isempty(e), error('JSON key %s is missing.',key); end
open=e; depth=0; inString=false; escaped=false; close=[];
for i=open:numel(json)
    c=json(i);
    if inString
        if escaped, escaped=false; elseif c=='\', escaped=true; elseif c=='"', inString=false; end
    else
        if c=='"', inString=true;
        elseif c=='{', depth=depth+1;
        elseif c=='}'
            depth=depth-1;
            if depth==0, close=i; break; end
        end
    end
end
if isempty(close), error('JSON block %s is incomplete.',key); end
block=json(open+1:close-1);
end

function p=resolveLineagePath(root,rel)
rel=char(rel);
% Stage 10 uses this key prefix to label source images; it is not a directory.
if startsWith(rel,'program_images/'), rel=rel(numel('program_images/')+1:end); end
if startsWith(rel,'xsim/') || startsWith(rel,'verilator/')
    rel=fullfile('reports','stage9_coverage',strrep(rel,'/',filesep));
end
p=fullfile(root,strrep(rel,'/',filesep));
end

function h=sha256File(path)
fid=fopen(path,'rb'); if fid<0, error('Cannot open hash input %s.',path); end
c=onCleanup(@()fclose(fid)); bytes=fread(fid,Inf,'*uint8');
md=java.security.MessageDigest.getInstance('SHA-256'); md.update(typecast(bytes(:),'int8'));
digest=typecast(md.digest(),'uint8'); h=lower(reshape(dec2hex(digest,2)',1,[]));
end

function h=sha256NormalizedTextFile(path)
text=fileread(path);
text=replace(text,sprintf('\r\n'),sprintf('\n'));
text=replace(text,sprintf('\r'),sprintf('\n'));
md=java.security.MessageDigest.getInstance('SHA-256');
md.update(typecast(uint8(unicode2native(text,'UTF-8')),'int8'));
digest=typecast(md.digest(),'uint8'); h=lower(reshape(dec2hex(digest,2)',1,[]));
end

function rows=appendStruct(rows,row)
if isempty(rows), rows=row; else, rows(end+1)=row; end
end

function rows=appendStructArray(rows,additions)
if isempty(additions), return; end
if isempty(rows), rows=additions; else, rows=[rows,additions]; end
end

function x=toNumeric(v)
if isnumeric(v) || islogical(v), x=double(v(:)); else, x=str2double(string(v(:))); end
end

function p=sigmoid(z)
z=max(min(z,35),-35); p=1./(1+exp(-z));
end

function writeStructTable(path,rows)
if isempty(rows), error('Required output table is empty: %s',path); end
writetable(struct2table(rows,'AsArray',true),path,'WriteVariableNames',true);
end

function writeText(path,text)
fid=fopen(path,'w'); if fid<0, error('Cannot write %s.',path); end
c=onCleanup(@()fclose(fid)); fwrite(fid,char(text),'char');
end
