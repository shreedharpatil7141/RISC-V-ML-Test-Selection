function stage12_run(mode)
% Offline Stage 12 selector over frozen Stage 10/11 artifacts.
if nargin<1, mode="run"; end
root=pwd; outDir=fullfile(root,'reports','stage12_test_selection');
if string(mode)=="run", runStage12(root,outDir); else, validateStage12(root,outDir); end
end

function seq=select(ids,P,valid,cost,initialCovered,alpha,budget,maxCount,mode,oracleY,staticScore,seed)
% Pure selection interface: predicted modes receive no actual labels or actual costs.
ids=string(ids(:)); n=numel(ids); if size(P,1)~=n || size(valid,1)~=n || numel(cost)~=n, error('Selector row alignment error.'); end
if any(~isfinite(cost)) || any(cost<0) || ~isfinite(budget) || budget<0, error('Invalid predicted budget.'); end
if mode=="oracle" && ~isequal(size(oracleY),size(P)), error('Oracle label alignment error.'); end
remaining=double(~initialCovered(:))'; chosen=false(n,1); selected=[]; attempts=struct([]); spent=0; tieCount=0;
if mode=="random", rng(seed,'twister'); perm=randperm(n); randomRank=zeros(n,1); randomRank(perm)=1:n; else, randomRank=zeros(n,1); end
while numel(selected)<min(maxCount,n)
    available=find(~chosen); if isempty(available), break; end
    gains=zeros(numel(available),1);
    if mode=="predicted"
        q=P(available,:); q(~isfinite(q) | ~valid(available,:))=0; gains=sum(q.*remaining,2);
        scores=gains./max(cost(available),1e-6).^alpha;
    elseif mode=="oracle"
        q=double(oracleY(available,:)==1 & valid(available,:)); gains=sum(q.*remaining,2);
        scores=gains./max(cost(available),1e-6).^alpha;
    elseif mode=="static"
        scores=staticScore(available); gains=scores;
    elseif mode=="random"
        scores=-randomRank(available); gains=scores;
    else, error('Unknown selection mode %s.',mode);
    end
    scoreMax=max(scores); tied=find(abs(scores-scoreMax)<=1e-12);
    if mode=="random"
        pick=available(find(randomRank(available)==min(randomRank(available)),1));
    elseif numel(tied)>1
        tieCount=tieCount+1; [~,ord]=sort(ids(available(tied))); pick=available(tied(ord(1)));
    else, pick=available(tied(1)); end
    jj=find(available==pick,1); decision="selected"; rank=numel(selected)+1;
    if spent+cost(pick)>budget+1e-9, decision="rejected_predicted_budget"; rank=0; end
    rec=struct('test_id',ids(pick),'rank',rank,'decision',decision,'score',scores(jj), ...
        'predicted_marginal_gain',gains(jj),'predicted_cycles',cost(pick), ...
        'predicted_cumulative_cycles',spent+cost(pick),'predicted_budget_cycles',budget, ...
        'predicted_budget_remaining',budget-spent-cost(pick),'cost_exponent',alpha, ...
        'selection_mode',mode,'tie_count_so_far',tieCount);
    attempts=appendStruct(attempts,rec); chosen(pick)=true;
    if decision=="selected"
        selected(end+1)=pick; spent=spent+cost(pick); %#ok<AGROW>
        if mode=="predicted"
            q=P(pick,:); q(~isfinite(q) | ~valid(pick,:))=0; remaining=remaining.*(1-q);
        elseif mode=="oracle"
            q=double(oracleY(pick,:)==1 & valid(pick,:)); remaining=remaining.*(1-q);
        end
    end
end
seq=struct('indices',selected(:),'ids',ids(selected),'attempts',attempts, ...
    'predictedSpent',spent,'budget',budget,'maxCount',maxCount,'alpha',alpha,'mode',mode,'seed',seed);
end

function [orders,curves,summaries]=addRun(orders,curves,summaries,scope,sim,method,seed,seq,x,pool,initialCovered,reach,rare,budget)
for k=1:numel(seq.attempts)
    a=seq.attempts(k); orders=appendStruct(orders,struct('scope',scope,'simulator',sim,'method',method, ...
        'seed',seed,'rank',a.rank,'test_id',a.test_id,'decision',a.decision,'predicted_score',a.score, ...
        'predicted_marginal_gain',a.predicted_marginal_gain,'predicted_cycles',a.predicted_cycles, ...
        'predicted_cumulative_cycles',a.predicted_cumulative_cycles,'predicted_budget_cycles',budget, ...
        'predicted_budget_remaining',a.predicted_budget_remaining,'cost_exponent',seq.alpha, ...
        'test_count_budget',seq.maxCount,'predicted_budget_rejections',sum(string({seq.attempts.decision})=="rejected_predicted_budget"), ...
        'cost_unit',"cycle", ...
        'actual_cycles_used_for_decision',false,'selection_mode',seq.mode));
end
ev=evaluate(seq,x,pool,initialCovered,reach,rare);
for k=1:numel(ev.curve)
    r=ev.curve(k); curves=appendStruct(curves,struct('scope',scope,'simulator',sim,'method',method, ...
        'seed',seed,'selected_count',r.count,'new_bins_this_step',r.newBins, ...
        'predicted_cycles_cumulative',r.predictedCost,'observed_cycles_cumulative_evaluation_only',r.actualCost, ...
        'predicted_budget_cycles',budget,'actual_budget_overrun_cycles_evaluation_only',max(0,r.actualCost-budget), ...
        'prediction_budget_overrun_evaluation_only',r.actualCost>budget+1e-9, ...
        'reachable_covered_bins',r.covered,'reachable_denominator',r.den, ...
        'reachable_coverage_fraction',safeDivide(r.covered,r.den), ...
        'rare_bins_covered',r.rareCovered,'rare_bins_denominator',r.rareDen, ...
        'rare_retention_fraction',safeDivide(r.rareCovered,r.rareDen)));
end
summaries=appendStruct(summaries,struct('scope',scope,'simulator',sim,'method',method,'seed',seed, ...
    'candidate_count',numel(pool),'selected_count',numel(seq.indices), ...
    'predicted_cycle_budget',budget,'predicted_cycles_spent',seq.predictedSpent, ...
    'actual_cycles_spent_evaluation_only',ev.actualCost, ...
    'actual_budget_overrun_cycles_evaluation_only',max(0,ev.actualCost-budget), ...
    'predicted_budget_rejections',sum(string({seq.attempts.decision})=="rejected_predicted_budget"), ...
    'prediction_budget_overrun',ev.actualCost>budget+1e-9,'new_covered_bins',ev.newBins, ...
    'reachable_covered_bins',ev.covered,'reachable_denominator',ev.den, ...
    'reachable_coverage_fraction',ev.coverage,'rare_bins_covered',ev.rareCovered, ...
    'rare_bins_denominator',ev.rareDen,'rare_retention_fraction',safeDivide(ev.rareCovered,ev.rareDen), ...
    'train_predictions_in_sample',scope=="full_corpus_replay_train_in_sample"));
end

function ev=evaluate(seq,x,pool,initialCovered,reach,rare)
covered=logical(initialCovered(:)); initial=covered; actualCost=0; predCost=0; curve=struct([]);
den=sum(reach); rareDen=sum(rare & reach);
curve=appendStruct(curve,struct('count',0,'newBins',0,'predictedCost',0,'actualCost',0, ...
    'covered',sum(covered & reach),'den',den,'rareCovered',sum(covered & rare & reach),'rareDen',rareDen));
for k=1:numel(seq.indices)
    i=pool(seq.indices(k)); hit=x.valid(i,:)' & x.reachable(:) & x.Y(i,:)'==1;
    new=hit & ~covered; covered=covered | hit; actualCost=actualCost+x.costActual(i); predCost=predCost+x.costPred(i);
    curve=appendStruct(curve,struct('count',k,'newBins',sum(new & reach), ...
        'predictedCost',predCost,'actualCost',actualCost,'covered',sum(covered & reach), ...
        'den',den,'rareCovered',sum(covered & rare & reach),'rareDen',rareDen));
end
ev=struct('curve',curve,'den',den,'covered',sum(covered & reach), ...
    'newBins',sum(covered & reach)-sum(initial & reach),'coverage',safeDivide(sum(covered & reach),den), ...
    'actualCost',actualCost,'rareCovered',sum(covered & rare & reach),'rareDen',rareDen);
end

function [F,S,L,D,C,P,CP,bundle,hashes]=loadInputs(root)
d=fullfile(root,'reports','stage10_dataset'); s=fullfile(root,'reports','stage11_matlab_ml');
stage10Manifest=fileread(fullfile(d,'manifest.json')); hashes=struct('path',{},'sha256',{});
hashes(end+1)=struct('path',"reports/stage10_dataset/manifest.json",'sha256',sha256PortableOutput(fullfile(d,'manifest.json')));
blk=extractJsonBlock(stage10Manifest,'csv_outputs'); e=regexp(blk,'"([^\"]+\.csv)"\s*:\s*\{\s*"rows"\s*:\s*(\d+)\s*,\s*"sha256"\s*:\s*"([0-9a-f]{64})"','tokens');
if numel(e)~=10 || ~contains(stage10Manifest,'"schema_version": "stage10-dataset-1.0.0"'), error('Frozen Stage 10 manifest/schema invalid.'); end
for k=1:numel(e)
    p=fullfile(d,e{k}{1}); if ~isfile(p) || ~strcmpi(sha256NormalizedTextFile(p),e{k}{3}), error('Stage 10 hash mismatch: %s',e{k}{1}); end
    hashes(end+1)=struct('path',["reports/stage10_dataset/"+e{k}{1}],'sha256',e{k}{3}); %#ok<AGROW>
end
F=readtable(fullfile(d,'features.csv'),'TextType','string','VariableNamingRule','preserve');
S=readtable(fullfile(d,'split_assignments.csv'),'TextType','string','VariableNamingRule','preserve');
L=readtable(fullfile(d,'coverage_labels.csv'),'TextType','string','VariableNamingRule','preserve');
D=readtable(fullfile(d,'bin_dictionary.csv'),'TextType','string','VariableNamingRule','preserve');
C=readtable(fullfile(d,'execution_costs.csv'),'TextType','string','VariableNamingRule','preserve');
smPath=fullfile(s,'manifest.json'); sm=jsondecode(fileread(smPath));
if sm.schema_version~="stage11-matlab-ml-1.0.0" || sm.base_commit~="2d195e581075c1a4cb7bb17d172d22a7472a8a9b"
    error('Stage 11 manifest lineage mismatch.');
end
hashes(end+1)=struct('path',"reports/stage11_matlab_ml/manifest.json",'sha256',sha256PortableOutput(smPath));
ks=fieldnames(sm.output_files);
for k=1:numel(ks)
    o=sm.output_files.(ks{k}); p=fullfile(s,o.path);
    if ~isfile(p) || ~strcmpi(sha256Stage11Output(p,o.path),o.sha256), error('Stage 11 artifact hash mismatch: %s',o.path); end
    hashes(end+1)=struct('path',["reports/stage11_matlab_ml/"+o.path],'sha256',sha256PortableOutput(p)); %#ok<AGROW>
end
for k=1:numel(sm.input_hashes)
    rel=string(sm.input_hashes(k).path); p=resolveStage11Input(root,rel);
    if startsWith(rel,"reports/stage10_dataset/") && endsWith(rel,".csv")
        ih=sha256NormalizedTextFile(p);
    elseif endsWith(rel,".m") || endsWith(rel,".bat")
        ih=sha256NormalizedTextFile(p);
    else
        ih=sha256File(p);
    end
    if ~isfile(p) || ~strcmpi(ih,sm.input_hashes(k).sha256), error('Stage 11 lineage input hash mismatch: %s',rel); end
end
P=readtable(fullfile(s,'predictions.csv'),'TextType','string','VariableNamingRule','preserve');
CP=readtable(fullfile(s,'cycle_predictions.csv'),'TextType','string','VariableNamingRule','preserve');
P=P(:,{'test_id','simulator','bin_id','split','applicable','available','calibrated_probability'});
CP=CP(:,{'test_id','simulator','split','predicted_cycles'});
bundle=load(fullfile(s,'models.mat'),'coverageModels','costModels','preprocess');
for rel=["scripts/machine_learning/stage11_run.m","scripts/machine_learning/run_stage11_matlab.bat", ...
        "scripts/machine_learning/validate_stage11_matlab.bat","reports/stage11_matlab_ml/metrics_per_bin.csv"]
    p=fullfile(root,strrep(rel,'/',filesep)); hashes(end+1)=struct('path',rel,'sha256',sha256PortableOutput(p)); %#ok<AGROW>
end
for rel=["scripts/machine_learning/stage12_run.m","scripts/machine_learning/run_stage12_matlab.bat", ...
        "scripts/machine_learning/validate_stage12_matlab.bat"]
    p=fullfile(root,strrep(rel,'/',filesep)); hashes(end+1)=struct('path',rel,'sha256',sha256PortableOutput(p)); %#ok<AGROW>
end
end

function x=buildSim(sim,F,ids,split,L,D,C,P,CP,bundle,bins)
n=numel(ids); b=numel(bins); q=string(L.simulator)==sim; T=L(q,:);
if height(T)~=n*b || ...
        any(~ismember(string(T.test_id),ids)) || any(~ismember(string(T.bin_id),bins))
    error('%s label alignment or IDs invalid.',sim);
end
Y=NaN(n,b); valid=false(n,b); appMat=false(n,b); availMat=false(n,b);
stateMat=repmat("unavailable",n,b);
app=toNumeric(T.applicable); av=toNumeric(T.available); val=toNumeric(T.value);
if any(~ismember(app,[0 1])) || any(~ismember(av,[0 1])) || any(app==0 & av~=0) || ...
        any(app==1 & av==1 & ~ismember(val,[0 1])), error('%s applicability/label masks invalid.',sim); end
state=string(T.state);
if any(app==0 & ~ismember(state,["inapplicable","unsupported"])) || ...
        any(app==1 & av==0 & state~="unavailable") || ...
        any(app==1 & av==1 & ~ismember(state,["observed_zero","observed_hit"])) || ...
        any((app==0 | av==0) & isfinite(val))
    error('%s observed/unavailable/inapplicable/unsupported states are inconsistent.',sim);
end
[~,ii]=ismember(string(T.test_id),ids); [~,jj]=ismember(string(T.bin_id),bins);
if any(ii==0)||any(jj==0), error('Unknown label key.'); end
key=sub2ind([n,b],ii,jj); if numel(unique(key))~=n*b, error('Duplicate or missing test/bin label pair.'); end
Y(key)=val; appMat(key)=app==1; availMat(key)=av==1; stateMat(key)=state;
valid(key)=app==1 & av==1 & isfinite(val);
score=NaN(n,b); q=string(P.simulator)==sim; PP=P(q,:); [ti,ri]=ismember(string(PP.test_id),ids); [bi,ci]=ismember(string(PP.bin_id),bins);
if any(~ti)||any(~bi), error('Stage 11 prediction alignment failed.'); end
% Import probabilities and masks only; actual_value and actual_state are intentionally ignored.
pp=toNumeric(PP.calibrated_probability); pa=toNumeric(PP.applicable); pv=toNumeric(PP.available);
for r=1:height(PP)
    if string(PP.split(r))~=split(ri(r)), error('Stage 11 prediction split mismatch for %s.',PP.test_id(r)); end
    if pa(r)~=double(appMat(ri(r),ci(r))) || pv(r)~=double(availMat(ri(r),ci(r)))
        error('Stage 11 prediction masks differ from Stage 10 for %s/%s/%s.',sim,PP.test_id(r),PP.bin_id(r));
    end
    if pa(r)==1 && pv(r)==1 && isfinite(pp(r)), score(ri(r),ci(r))=pp(r); end
end
if any(valid(split~="train",:) & ~isfinite(score(split~="train",:)),'all')
    warning('%s has unavailable Stage 11 scores; these targets are skipped.',sim);
end
raw=[toNumeric(F.program_bytes),toNumeric(F.unique_byte_values)]; cfg=string(F.configuration);
levels=string(bundle.preprocess.configuration_levels_from_training(:))';
X=[(raw-bundle.preprocess.training_mean)./bundle.preprocess.training_scale,double(cfg==levels)];
records=find(string({bundle.coverageModels.simulator})==sim);
for ri=records
    jj=find(bins==string(bundle.coverageModels(ri).bin_id),1); rows=find(split=="train" & valid(:,jj));
    if isempty(rows), continue; end
    candidate=bundle.coverageModels(ri).candidate_models(1);
    pr=applyCalibration(predictCandidate(candidate,X(rows,:)),bundle.coverageModels(ri).calibration);
    score(rows,jj)=pr;
end

q=string(C.simulator)==sim; CC=C(q,:); [tf,cl]=ismember(ids,string(CC.test_id)); if ~all(tf), error('Cost IDs misalign.'); end
CC=CC(cl,:); actualCost=toNumeric(CC.observed_cycles);
if any(~isfinite(actualCost)|actualCost<=0) || any(string(CC.status)~="PASS") || any(string(CC.cycles_unit)~="cycle")
    error('Observed cycle costs invalid for %s.',sim);
end
predCost=NaN(n,1); q=string(CP.simulator)==sim; Q=CP(q,:); [tf,pl]=ismember(string(Q.test_id),ids);
for r=1:height(Q)
    if tf(r) && string(Q.split(r))~="train"
        if string(Q.split(r))~=split(pl(r)), error('Stage 11 cost split mismatch for %s.',Q.test_id(r)); end
        predCost(pl(r))=toNumeric(Q.predicted_cycles(r));
    end
end
cm=find(string({bundle.costModels.simulator})==sim,1); if isempty(cm), error('Stage 11 cost model missing for %s.',sim); end
tr=find(split=="train"); predCost(tr)=predictCost(bundle.costModels(cm).model,X(tr,:)); predCost=max(predCost,1e-6);
if any(~isfinite(predCost)), error('Predicted cycles invalid for %s.',sim); end
[rd,rl]=ismember(bins,string(D.bin_id)); if ~all(rd), error('Reachability dictionary does not align.'); end
reach=string(D.reachability(rl))=="reachable" & any(valid,1)'; rare=false(b,1);
MD=readtable(fullfile(pwd,'reports','stage11_matlab_ml','metrics_per_bin.csv'),'TextType','string','VariableNamingRule','preserve');
MD=MD(string(MD.simulator)==sim,:); [ok,mLoc]=ismember(bins,string(MD.bin_id)); if all(ok), rare=toNumeric(MD.rare_positive(mLoc))==1 & reach; end
static=toNumeric(F.program_bytes)+toNumeric(F.unique_byte_values);
x=struct('sim',sim,'ids',ids,'split',split,'P',score,'valid',valid, ...
    'scoreValid',valid & isfinite(score) & reach(:)','app',appMat,'evidenceAvailable',availMat, ...
    'state',stateMat,'Y',Y,'bins',bins, ...
    'costPred',predCost,'costActual',actualCost,'static',static,'reachable',reach,'rare',rare);
end

function rows=candidateExport(data)
rows=table();
for si=1:numel(data), x=data(si); [ri,bi]=ndgrid(1:numel(x.ids),1:numel(x.bins)); ri=ri(:); bi=bi(:);
    t=table(x.ids(ri),repmat(x.sim,numel(ri),1),x.split(ri),x.bins(bi), ...
        x.app(sub2ind(size(x.app),ri,bi)),x.evidenceAvailable(sub2ind(size(x.app),ri,bi)), ...
        isfinite(x.P(sub2ind(size(x.P),ri,bi))),x.P(sub2ind(size(x.P),ri,bi)), ...
        x.reachable(bi),x.rare(bi),false(numel(ri),1),x.split(ri)=="train", ...
        'VariableNames',{'test_id','simulator','split','bin_id','applicable','evidence_available', ...
        'prediction_available','predicted_hit_probability','reachable','rare_bin','actual_label_included','train_prediction_in_sample'});
    rows=[rows;t]; %#ok<AGROW>
end
end

function rows=observationExport(data)
rows=table();
for si=1:numel(data), x=data(si); [ri,bi]=ndgrid(1:numel(x.ids),1:numel(x.bins)); ri=ri(:); bi=bi(:); ix=sub2ind(size(x.Y),ri,bi);
    t=table(x.ids(ri),repmat(x.sim,numel(ri),1),x.split(ri),x.bins(bi),x.state(ix),x.Y(ix), ...
        x.app(ix),x.evidenceAvailable(ix),true(numel(ri),1), ...
        'VariableNames',{'test_id','simulator','split','bin_id','state','value','applicable','evidence_available','evaluation_only'});
    rows=[rows;t]; %#ok<AGROW>
end
end

function rows=costExport(data)
rows=table();
for si=1:numel(data), x=data(si); n=numel(x.ids);
    t=table(x.ids,repmat(x.sim,n,1),x.split,x.costPred,x.costActual,repmat("cycle",n,1), ...
        repmat("Stage 11 frozen model",n,1),repmat("Stage 10 validated measurement",n,1),true(n,1), ...
        'VariableNames',{'test_id','simulator','split','predicted_cycles','observed_cycles_evaluation_only', ...
        'unit','predicted_cost_source','observed_cost_source','observed_cost_evaluation_only'});
    rows=[rows;t]; %#ok<AGROW>
end
end

function m=makeManifest(~,outDir,hashes)
files=dir(fullfile(outDir,'*')); outputs=struct();
for k=1:numel(files)
    if files(k).isdir || files(k).name=="manifest.json", continue; end
    key=matlab.lang.makeValidName(strrep(files(k).name,'.','_'));
    outputs.(key)=struct('path',files(k).name,'sha256',sha256PortableOutput(fullfile(outDir,files(k).name)));
end
m=struct('schema_version',"stage12-selection-1.0.0",'base_commit',"b0856cc6f7e954908f266ee0bf31299542aec3c2", ...
    'input_hashes',hashes,'output_files',outputs,'validation_status',"PASS",'logical_tests',282, ...
    'split_sizes',struct('train',196,'validation',46,'test',40),'simulator_rows_pooled',false, ...
    'actual_test_cost_used_for_budget',false,'generalization_claim',false,'superiority_claim',false);
end

function p=predictCandidate(c,X)
switch c.type
    case "constant", p=repmat(c.probability,size(X,1),1);
    case {"fitctree","fitcnb","TreeBagger"}
        [~,sc]=predict(c.model,X); ix=find(string(c.model.ClassNames(:))=="1",1);
        if isempty(ix), p=zeros(size(X,1),1); else, p=sc(:,ix); end
    case "logistic", z=[ones(size(X,1),1),X]*c.model; p=1./(1+exp(-max(min(z,35),-35)));
    otherwise, error('Unsupported frozen classifier type %s.',c.type);
end
p=min(max(double(p(:)),1e-8),1-1e-8);
end
function p=applyCalibration(p,c)
p=min(max(p(:),1e-6),1-1e-6);
if string(c.method)=="validation_platt"
    z=log(p./(1-p)); p=1./(1+exp(-max(min(c.intercept+c.slope*z,35),-35)));
end
end
function y=predictCost(c,X)
switch c.type
    case "median", y=repmat(c.model,size(X,1),1);
    case "ridge", y=[ones(size(X,1),1),X]*c.model;
    case "tree", y=predict(c.model,X);
    otherwise, error('Unsupported frozen cost model type %s.',c.type);
end
y=max(double(y(:)),1e-6);
end
function h=sha256File(path)
fid=fopen(path,'rb'); if fid<0, error('Cannot open hash input %s.',path); end
c=onCleanup(@()fclose(fid)); bytes=fread(fid,Inf,'*uint8'); md=java.security.MessageDigest.getInstance('SHA-256');
md.update(typecast(bytes(:),'int8')); d=typecast(md.digest(),'uint8'); h=lower(reshape(dec2hex(d,2)',1,[]));
end
function h=sha256NormalizedTextFile(path)
t=fileread(path); t=replace(t,sprintf('\r\n'),sprintf('\n')); t=replace(t,sprintf('\r'),sprintf('\n'));
md=java.security.MessageDigest.getInstance('SHA-256'); md.update(typecast(uint8(unicode2native(t,'UTF-8')),'int8'));
d=typecast(md.digest(),'uint8'); h=lower(reshape(dec2hex(d,2)',1,[]));
end
function h=sha256Stage11Output(path,rel)
if endsWith(rel,'.json') || endsWith(rel,'.txt'), h=sha256NormalizedTextFile(path); else, h=sha256File(path); end
end
function h=sha256PortableOutput(path)
[~,~,ext]=fileparts(path);
if ismember(string(ext),[".csv",".json",".txt",".m",".bat",".md"]), h=sha256NormalizedTextFile(path); else, h=sha256File(path); end
end
function p=resolveStage11Input(root,rel)
rel=char(rel);
if startsWith(rel,'program_images/'), rel=rel(numel('program_images/')+1:end); end
if startsWith(rel,'xsim/') || startsWith(rel,'verilator/'), rel=fullfile('reports','stage9_coverage',strrep(rel,'/',filesep));
else, rel=strrep(rel,'/',filesep); end
p=fullfile(root,rel);
end
function b=extractJsonBlock(t,key)
n=['"' key '"']; p=strfind(t,n); if isempty(p), error('JSON key %s missing.',key); end
colon=p(1)+find(t(p(1):end)==':',1)-1; i=colon+find(~isspace(t(colon+1:end)),1);
if t(i)~='{', error('JSON object expected for %s.',key); end
depth=0; quoted=false; escaped=false;
for j=i:numel(t)
    ch=t(j);
    if quoted
        if escaped, escaped=false; elseif ch=='\', escaped=true; elseif ch=='"', quoted=false; end
    else
        if ch=='"', quoted=true; elseif ch=='{', depth=depth+1; elseif ch=='}', depth=depth-1; if depth==0, break; end; end
    end
end
b=t(i:j);
end
function x=toNumeric(v), if isnumeric(v)||islogical(v), x=double(v(:)); else, x=str2double(string(v(:))); end, end
function v=safeDivide(a,b), if b==0, v=NaN; else, v=a/b; end, end
function rows=appendStruct(rows,row), if isempty(rows), rows=row; else, rows(end+1)=row; end, end
function writeTable(path,rows)
if isempty(rows), error('Required output table empty: %s',path); end
if istable(rows), writetable(rows,path); else, writetable(struct2table(rows,'AsArray',true),path); end
end
function writeJson(path,obj), f=fopen(path,'w'); c=onCleanup(@()fclose(f)); fwrite(f,jsonencode(obj,'PrettyPrint',true),'char'); fwrite(f,newline,'char'); end
function writeText(path,text), f=fopen(path,'w'); c=onCleanup(@()fclose(f)); fwrite(f,text,'char'); end

function runStage12(root,outDir)
if ~license('test','Statistics_Toolbox'), error('Statistics and Machine Learning Toolbox license is required.'); end
if ~isfolder(outDir), mkdir(outDir); end
[F,S,L,D,C,P,CP,bundle,hashes]=loadInputs(root);
ids=string(F.test_id); loc=zeros(size(ids)); [ok,loc]=ismember(ids,string(S.test_id));
if ~all(ok) || numel(unique(ids))~=282 || numel(unique(string(S.test_id)))~=282, error('Stage 10 identity alignment failed.'); end
split=string(S.split(loc));
if sum(split=="train")~=196 || sum(split=="validation")~=46 || sum(split=="test")~=40
    error('Frozen split changed; expected 196/46/40.');
end
groups=string(S.group_id(loc));
for g=unique(groups)'
    if numel(unique(split(groups==g)))~=1, error('Related logical tests cross the frozen split: %s.',g); end
end
simulators=["xsim","verilator"]; bins=sort(string(D.bin_id)); data=struct([]);
for si=1:numel(simulators)
    data=appendStruct(data,buildSim(simulators(si),F,ids,split,L,D,C,P,CP,bundle,bins));
end
alphas=[0 0.5 1]; fractions=[0.25 0.5 0.75 1]; countCaps=[5 10 20 40]; seeds=1201:1220;
orders=struct([]); curves=struct([]); tune=struct([]); choices=struct([]); summaries=struct([]);
for si=1:numel(data)
    x=data(si); sim=x.sim; tr=x.split=="train"; va=x.split=="validation"; te=x.split=="test";
    trainCovered=any(x.Y(tr,:)==1 & x.valid(tr,:),1)' & x.reachable(:);
    baseVal=sum(x.costPred(va)); best=struct('hits',-1,'actual',Inf,'alpha',NaN,'fraction',NaN,'cap',NaN);
    for alpha=alphas
        for frac=fractions
            for cap=countCaps
                budget=baseVal*frac; pool=find(va);
                seq=select(x.ids(pool),x.P(pool,:),x.scoreValid(pool,:),x.costPred(pool),trainCovered, ...
                    alpha,budget,cap,"predicted",[],x.static(pool),0);
                ev=evaluate(seq,x,pool,trainCovered,x.reachable,x.rare);
                tune=appendStruct(tune,struct('simulator',sim,'cost_exponent',alpha,'budget_fraction',frac, ...
                    'predicted_cycle_budget',budget,'count_cap',cap,'selected_count',numel(seq.ids), ...
                    'new_bins',ev.newBins,'reachable_denominator',ev.den,'coverage_fraction',ev.coverage, ...
                    'validation_actual_cycles',ev.actualCost, ...
                    'validation_actual_budget_overrun_cycles',max(0,ev.actualCost-budget), ...
                    'validation_prediction_budget_overrun',ev.actualCost>budget+1e-9));
                if ev.newBins>best.hits || (ev.newBins==best.hits && ev.actualCost<best.actual) || ...
                    (ev.newBins==best.hits && ev.actualCost==best.actual && frac<best.fraction)
                    best=struct('hits',ev.newBins,'actual',ev.actualCost,'alpha',alpha,'fraction',frac,'cap',cap);
                end
            end
        end
    end
    choices=appendStruct(choices,struct('simulator',sim,'cost_exponent',best.alpha, ...
        'budget_fraction',best.fraction,'count_cap',best.cap,'validation_new_bins',best.hits, ...
        'validation_actual_cycles',best.actual,'choice_rule',"validation_max_new_bins_then_lower_actual_cycles"));

    % Build every held-out predicted policy before evaluating any test outcomes.
    testPool=find(te); hist=trainCovered | (any(x.Y(va,:)==1 & x.valid(va,:),1)' & x.reachable(:));
    testBudget=sum(x.costPred(te))*best.fraction;
    predSeq=select(x.ids(testPool),x.P(testPool,:),x.scoreValid(testPool,:),x.costPred(testPool),hist, ...
        best.alpha,testBudget,best.cap,"predicted",[],x.static(testPool),0);
    noCost=select(x.ids(testPool),x.P(testPool,:),x.scoreValid(testPool,:),x.costPred(testPool),hist, ...
        0,testBudget,best.cap,"predicted",[],x.static(testPool),0);
    staticSeq=select(x.ids(testPool),x.P(testPool,:),x.valid(testPool,:),x.costPred(testPool),hist, ...
        best.alpha,testBudget,best.cap,"static",[],x.static(testPool),0);
    oracleY=double(x.Y(testPool,:)==1 & x.valid(testPool,:));
    oracleSeq=select(x.ids(testPool),x.P(testPool,:),x.valid(testPool,:) & x.reachable(:)',x.costPred(testPool),hist, ...
        best.alpha,testBudget,best.cap,"oracle",oracleY,x.static(testPool),0);
    [orders,curves,summaries]=addRun(orders,curves,summaries,"heldout_test",sim, ...
        "validation_selected_predicted",0,predSeq,x,testPool,hist,x.reachable,x.rare,testBudget);
    [orders,curves,summaries]=addRun(orders,curves,summaries,"heldout_test",sim, ...
        "predicted_no_cost",0,noCost,x,testPool,hist,x.reachable,x.rare,testBudget);
    [orders,curves,summaries]=addRun(orders,curves,summaries,"heldout_test",sim, ...
        "static_feature",0,staticSeq,x,testPool,hist,x.reachable,x.rare,testBudget);
    [orders,curves,summaries]=addRun(orders,curves,summaries,"heldout_test",sim, ...
        "oracle_actual_label_upper_bound",0,oracleSeq,x,testPool,hist,x.reachable,x.rare,testBudget);
    for seed=seeds
        randSeq=select(x.ids(testPool),x.P(testPool,:),x.valid(testPool,:),x.costPred(testPool),hist, ...
            best.alpha,testBudget,best.cap,"random",[],x.static(testPool),seed);
        [orders,curves,summaries]=addRun(orders,curves,summaries,"heldout_test",sim, ...
            "random",seed,randSeq,x,testPool,hist,x.reachable,x.rare,testBudget);
    end
    % Full-corpus replay is separate; train scores are explicitly in-sample.
    fullPool=(1:numel(x.ids))'; allBudget=sum(x.costPred)*best.fraction;
    fullSeq=select(x.ids,x.P,x.scoreValid,x.costPred,false(size(x.reachable)),best.alpha,allBudget, ...
        best.cap,"predicted",[],x.static,0);
    [orders,curves,summaries]=addRun(orders,curves,summaries, ...
        "full_corpus_replay_train_in_sample",sim,"validation_selected_predicted",0,fullSeq,x,fullPool, ...
        false(size(x.reachable)),x.reachable,x.rare,allBudget);
end

runtime=struct('release',string(version('-release')),'version',string(version), ...
    'statistics_toolbox_license',logical(license('test','Statistics_Toolbox')));
products=ver; pi=find(contains(string({products.Name}),"Statistics and Machine Learning Toolbox"),1);
if isempty(pi), error('Statistics and Machine Learning Toolbox is not installed.'); end
runtime.statistics_toolbox_name=string(products(pi).Name); runtime.statistics_toolbox_version=string(products(pi).Version);
configuration=struct('schema_version',"stage12-selection-1.0.0", ...
    'base_commit',"b0856cc6f7e954908f266ee0bf31299542aec3c2",'runtime',runtime, ...
    'logical_split',struct('train',196,'validation',46,'test',40),'simulators',simulators, ...
    'predictors',{{"program_bytes","unique_byte_values","configuration indicators"}}, ...
    'excluded_predictors',{{"test_id except stable join/tie-break","scenario","seed","family", ...
      "image hash","actual coverage","actual cycles","outcomes","provenance"}}, ...
    'gain_rule',"sum p_hit times residual expected-uncovered mass", ...
    'overlap_assumption',"independence approximation using marginal Stage 11 probabilities", ...
    'static_heuristic',"descending program_bytes plus unique_byte_values; stable ID tie-break", ...
    'cost_source',"frozen Stage 11 predicted observed_cycles; test actual cycles evaluation-only", ...
    'validation_alpha_grid',alphas,'validation_budget_fraction_grid',fractions, ...
    'validation_count_cap_grid',countCaps,'random_seeds',seeds, ...
    'oracle_baseline',"actual-label greedy; offline upper bound only", ...
    'full_corpus_note',"Train predictions are in-sample; held-out results are reported separately.", ...
    'limitations',"Exploratory small corpus; no savings, superiority, or generalization claim.");
writeTable(fullfile(outDir,'selection_order.csv'),orders);
writeTable(fullfile(outDir,'candidate_scores.csv'),candidateExport(data));
writeTable(fullfile(outDir,'evaluation_observations.csv'),observationExport(data));
writeTable(fullfile(outDir,'evaluation_costs.csv'),costExport(data));
writeTable(fullfile(outDir,'selection_curves.csv'),curves);
writeTable(fullfile(outDir,'validation_policy_grid.csv'),tune);
writeTable(fullfile(outDir,'policy_choices.csv'),choices);
writeTable(fullfile(outDir,'selection_summary.csv'),summaries);
writeTable(fullfile(outDir,'random_seed_variability.csv'),randomVariability(summaries));
writeJson(fullfile(outDir,'configuration.json'),configuration);
save(fullfile(outDir,'selection_replay.mat'),'orders','curves','tune','choices','summaries','-v7.3');
writeText(fullfile(outDir,'validation_evidence.txt'),sprintf(['STAGE12 MATLAB VALIDATION PASS\nrelease=%s\n' ...
    'logical_tests=282\ntrain_validation_test=196,46,40\nsimulators_separate=true\n' ...
    'test_actual_cost_used_for_budget=false\nselection_core_checks=PASS\nserialization_replay=PASS\n'],version('-release')));
manifest=makeManifest(root,outDir,hashes); writeJson(fullfile(outDir,'manifest.json'),manifest);
validateStage12(root,outDir);
end

function validateStage12(root,outDir)
mp=fullfile(outDir,'manifest.json'); if ~isfile(mp), error('Stage 12 manifest missing.'); end
m=jsondecode(fileread(mp));
if m.schema_version~="stage12-selection-1.0.0" || m.base_commit~="b0856cc6f7e954908f266ee0bf31299542aec3c2" || ...
        m.split_sizes.train~=196 || m.split_sizes.validation~=46 || m.split_sizes.test~=40 || m.simulator_rows_pooled
    error('Stage 12 lineage, schema, or frozen split invalid.');
end
for k=1:numel(m.input_hashes)
    rel=m.input_hashes(k).path; p=fullfile(root,strrep(rel,'/',filesep));
    h=sha256PortableOutput(p);
    if ~isfile(p) || ~strcmpi(h,m.input_hashes(k).sha256), error('Stage 12 input hash mismatch: %s',rel); end
end
ks=fieldnames(m.output_files);
for k=1:numel(ks)
    o=m.output_files.(ks{k}); p=fullfile(outDir,o.path);
    if ~isfile(p) || ~strcmpi(sha256PortableOutput(p),o.sha256), error('Stage 12 output hash mismatch: %s',o.path); end
end
orders=readtable(fullfile(outDir,'selection_order.csv'),'TextType','string','VariableNamingRule','preserve');
curves=readtable(fullfile(outDir,'selection_curves.csv'),'TextType','string','VariableNamingRule','preserve');
choices=readtable(fullfile(outDir,'policy_choices.csv'),'TextType','string','VariableNamingRule','preserve');
scores=readtable(fullfile(outDir,'candidate_scores.csv'),'TextType','string','VariableNamingRule','preserve');
obs=readtable(fullfile(outDir,'evaluation_observations.csv'),'TextType','string','VariableNamingRule','preserve');
costs=readtable(fullfile(outDir,'evaluation_costs.csv'),'TextType','string','VariableNamingRule','preserve');
variability=readtable(fullfile(outDir,'random_seed_variability.csv'),'TextType','string','VariableNamingRule','preserve');
if isempty(orders) || isempty(curves) || height(choices)~=2, error('Stage 12 exports incomplete.'); end
if height(scores)~=2*282*316 || height(obs)~=height(scores) || height(costs)~=564 || height(variability)~=2
    error('Stage 12 candidate/evaluation row counts are misaligned.');
end
scoreKey=string(scores.test_id)+"|"+string(scores.simulator)+"|"+string(scores.bin_id);
obsKey=string(obs.test_id)+"|"+string(obs.simulator)+"|"+string(obs.bin_id);
if numel(unique(scoreKey))~=height(scores) || ~isequal(scoreKey,obsKey), error('Stable test/bin rows are duplicated or misaligned.'); end
if any(toNumeric(scores.applicable)==0 & toNumeric(scores.evidence_available)==1) || ...
        any(toNumeric(scores.prediction_available)==0 & isfinite(toNumeric(scores.predicted_hit_probability)))
    error('Invalid applicability/availability/prediction masks in score export.');
end
if any(string(obs.state)=="observed_zero" & toNumeric(obs.value)~=0) || ...
        any(string(obs.state)=="observed_hit" & toNumeric(obs.value)~=1) || ...
        any(ismember(string(obs.state),["unavailable","inapplicable","unsupported"]) & isfinite(toNumeric(obs.value)))
    error('Observed outcome states were collapsed or misrepresented.');
end
if any(toNumeric(orders.actual_cycles_used_for_decision)~=0), error('Actual cycles leaked into a decision record.'); end
accepted=orders(string(orders.decision)=="selected",:);
grp=unique(string(accepted.scope)+"|"+string(accepted.simulator)+"|"+string(accepted.method)+"|"+string(accepted.seed));
for g=grp'
    q=string(accepted.scope)+"|"+string(accepted.simulator)+"|"+string(accepted.method)+"|"+string(accepted.seed)==g;
    if numel(unique(string(accepted.test_id(q))))~=sum(q), error('Duplicate ID selected in a run.'); end
    if any(diff(toNumeric(accepted.rank(q)))<=0), error('Selection ranks are not increasing.'); end
end
if any(toNumeric(accepted.predicted_cumulative_cycles)>toNumeric(accepted.predicted_budget_cycles)+1e-8)
    error('Predicted-cost budget overrun in accepted selections.');
end
for g=grp'
    q=string(accepted.scope)+"|"+string(accepted.simulator)+"|"+string(accepted.method)+"|"+string(accepted.seed)==g;
    if sum(q)>max(toNumeric(accepted.test_count_budget(q))), error('Test-count budget exceeded.'); end
end
runSelectorExamples();
saved=load(fullfile(outDir,'selection_replay.mat'),'orders');
R=struct2table(saved.orders,'AsArray',true);
if height(R)~=height(orders) || ~isequal(string(R.test_id),string(orders.test_id)) || ...
        ~isequal(string(R.decision),string(orders.decision))
    error('Selection MAT/CSV serialization replay mismatch.');
end
cfg=jsondecode(fileread(fullfile(outDir,'configuration.json')));
if cfg.runtime.release~=string(version('-release')) || ~cfg.runtime.statistics_toolbox_license
    error('Runtime/dependency configuration incomplete.');
end
fprintf('STAGE12 VALIDATION PASS release=%s orders=%d curves=%d policies=%d\n', ...
    version('-release'),height(orders),height(curves),height(choices));
end

function runSelectorExamples()
% Deterministic tie, overlap, mask, budget-boundary, unavailable, duplicate, random checks.
a=select(["b";"a"],[1;1],true(2,1),[1;1],false,0,1,1,"predicted",[],[0;0],0);
if numel(a.ids)~=1 || a.ids(1)~="a", error('Stable ID tie-break example failed.'); end
P=[1 0;0.9 0.2;0 1];
b=select(["A";"B";"C"],P,true(3,2),ones(3,1),false(2,1),0,3,2,"predicted",[],zeros(3,1),0);
if ~isequal(b.ids,["B";"C"]), error('Expected-overlap marginal example failed.'); end
mask=[true false;true true]; c=select(["masked";"valid"],[1 1;0.2 0],mask,[1;1],false(2,1),0,2,1,"predicted",[],[0;0],0);
if c.ids(1)~="masked" || c.attempts(1).predicted_marginal_gain~=1, error('Mask accounting example failed.'); end
d=select(["too_costly";"boundary"],[1;0.5],true(2,1),[1.01;1],false,0,1,1,"predicted",[],[0;0],0);
if ~isequal(d.ids,"boundary") || ~any(string({d.attempts.decision})=="rejected_predicted_budget"), error('Budget boundary example failed.'); end
e=select(["missing";"observed"],[NaN;0.4],[false;true],[1;1],false,0,1,1,"predicted",[],[0;0],0);
if e.ids(1)~="observed", error('Unavailable target example failed.'); end
if numel(unique(e.ids))~=numel(e.ids), error('Duplicate selection prevention example failed.'); end
r1=select(["A";"B";"C"],[0;0;0],false(3,1),ones(3,1),false,0,3,3,"random",[],zeros(3,1),41);
r2=select(["A";"B";"C"],[0;0;0],false(3,1),ones(3,1),false,0,3,3,"random",[],zeros(3,1),41);
if ~isequal(r1.ids,r2.ids), error('Random seed replay example failed.'); end
end

function rows=randomVariability(summaries)
rows=struct([]); for sim=["xsim","verilator"]
    q=string({summaries.scope})=="heldout_test" & string({summaries.simulator})==sim & string({summaries.method})=="random";
    hits=[summaries(q).new_covered_bins]; costs=[summaries(q).actual_cycles_spent_evaluation_only];
    overruns=[summaries(q).actual_budget_overrun_cycles_evaluation_only]; flags=[summaries(q).prediction_budget_overrun];
    rows=appendStruct(rows,struct('simulator',sim,'seed_count',numel(hits), ...
        'new_covered_bins_mean',mean(hits),'new_covered_bins_std',std(hits,0), ...
        'observed_cycles_mean_evaluation_only',mean(costs),'observed_cycles_std_evaluation_only',std(costs,0), ...
        'budget_overrun_seed_count',sum(flags),'budget_overrun_rate',mean(flags), ...
        'actual_budget_overrun_cycles_mean',mean(overruns),'actual_budget_overrun_cycles_max',max(overruns)));
end
end
