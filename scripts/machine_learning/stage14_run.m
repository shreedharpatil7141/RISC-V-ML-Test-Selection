function stage14_run(mode)
% Stage 14 comparative offline replay. Configuration is saved before replay.
if nargin==0, mode="run"; end
root=pwd; out=fullfile(root,'reports','stage14_experiments');
if string(mode)=="run", runBatch(root,out); elseif string(mode)=="validate", validateBatch(root,out); elseif string(mode)=="check_dictionary", checkDictionary(root); elseif string(mode)=="check_mask_audit", checkMaskAudit(root,out); elseif string(mode)=="check_selection", checkSelectionLoops(); else, error('Mode must be run, validate, check_dictionary, check_mask_audit, or check_selection.'); end
end

function runBatch(root,out)
batchClock=tic;
validateMaskFixtures();
cfg=jsondecode(fileread(fullfile(out,'configuration.json')));
if cfg.frozen_split.train~=196 || cfg.frozen_split.validation~=46 || cfg.frozen_split.test~=40
    error('Pre-registered split changed.');
end
% Freeze source hashes into the preregistration before any replay begins.
files={"reports/stage10_dataset/manifest.json","reports/stage10_dataset/split_assignments.csv", ...
 "reports/stage10_dataset/features.csv","reports/stage10_dataset/coverage_labels.csv", ...
 "reports/stage10_dataset/bin_dictionary.csv","reports/stage10_dataset/execution_costs.csv", ...
 "reports/stage11_matlab_ml/predictions.csv","reports/stage11_matlab_ml/cycle_predictions.csv", ...
 "reports/stage11_matlab_ml/cycle_cost_metrics.csv","reports/stage11_matlab_ml/metrics_per_bin.csv", ...
 "reports/stage11_matlab_ml/models.mat","reports/stage11_matlab_ml/manifest.json", ...
 "reports/stage12_test_selection/selection_curves.csv","reports/stage12_test_selection/manifest.json", ...
 "reports/stage13_active_learning/learning_curves.csv","reports/stage13_active_learning/manifest.json"};
for k=1:numel(files), cfg.input_hashes(k)=struct('path',files{k},'sha256',sha(fullfile(root,strrep(files{k},'/',filesep)))); end
cfg.runtime=struct('release',version('-release'),'version',version,'toolboxes',ver);
writeJson(fullfile(out,'configuration.json'),cfg); % written before replay

d10=fullfile(root,'reports','stage10_dataset');
F=readtable(fullfile(d10,'features.csv'),'TextType','string','VariableNamingRule','preserve');
S=readtable(fullfile(d10,'split_assignments.csv'),'TextType','string','VariableNamingRule','preserve');
L=readtable(fullfile(d10,'coverage_labels.csv'),'TextType','string','VariableNamingRule','preserve');
D=readtable(fullfile(d10,'bin_dictionary.csv'),'TextType','string','VariableNamingRule','preserve');
C=readtable(fullfile(d10,'execution_costs.csv'),'TextType','string','VariableNamingRule','preserve');
P=readtable(fullfile(root,'reports','stage11_matlab_ml','predictions.csv'),'TextType','string','VariableNamingRule','preserve');
CP=readtable(fullfile(root,'reports','stage11_matlab_ml','cycle_predictions.csv'),'TextType','string','VariableNamingRule','preserve');
ids=string(F.test_id); [tf,si]=ismember(ids,string(S.test_id)); if ~all(tf), error('Split IDs misaligned.'); end
src=jsondecode(fileread(fullfile(d10,'manifest.json'))); names=fieldnames(src.csv_outputs);
for k=1:numel(names), fn=strrep(names{k},'_csv','.csv'); if ~strcmpi(src.csv_outputs.(names{k}).sha256,sha(fullfile(d10,fn))),error('Stage 10 manifest hash mismatch: %s',fn);end,end
split=string(S.split(si)); group=string(S.group_id(si));
if sum(split=="train")~=196||sum(split=="validation")~=46||sum(split=="test")~=40,error('Frozen 196/46/40 split mismatch.');end
for g=unique(group)',if numel(unique(split(group==g)))~=1,error('Split isolation violated for group %s',g);end,end
if height(F)~=282||numel(unique(ids))~=282,error('Logical dataset count/IDs invalid.');end
% The Stage 11 cycle_predictions export intentionally contains validation/test
% only. Apply the frozen selected cost model to train candidates, with no refit.
s11m=jsondecode(fileread(fullfile(root,'reports','stage11_matlab_ml','manifest.json')));
modelPath=fullfile(root,'reports','stage11_matlab_ml','models.mat');
if ~isfield(s11m.output_files,'models_mat')||~strcmpi(sha(modelPath),s11m.output_files.models_mat.sha256),error('Frozen Stage 11 cost-model hash mismatch.');end
bundle=load(modelPath,'costModels','preprocess');
if numel(bundle.costModels)~=2||bundle.preprocess.fit_scope~="train_only"||~isequal(string(bundle.preprocess.train_ids(:)),ids(split=="train")),error('Frozen Stage 11 cost-model lineage/split invalid.');end
verifyStage11Outputs(root,s11m);
costAudit=buildTrainingCostJoin(F,ids,split,CP,bundle.costModels,bundle.preprocess);
writeStruct(fullfile(out,'cost_join_audit.csv'),costAudit);
stage13Manifest=jsondecode(fileread(fullfile(root,'reports','stage13_active_learning','manifest.json')));
stage13Curve=stage13Manifest.outputs(string({stage13Manifest.outputs.path})=="learning_curves.csv");
if numel(stage13Curve)~=1||~strcmpi(sha(fullfile(root,'reports','stage13_active_learning','learning_curves.csv')),stage13Curve.sha256),error('Stage 13 learning_curves input hash mismatch.');end
stage12Manifest=jsondecode(fileread(fullfile(root,'reports','stage12_test_selection','manifest.json')));
stage12Curve=stage12Manifest.output_files.selection_curves_csv;
if ~strcmpi(sha(fullfile(root,'reports','stage12_test_selection','selection_curves.csv')),stage12Curve.sha256),error('Stage 12 selection_curves input hash mismatch.');end
[bins,reachText,reach]=validateDictionary(D);
% Rarity is frozen in Stage 11's per-bin training support metadata.
MD=readtable(fullfile(root,'reports','stage11_matlab_ml','metrics_per_bin.csv'),'TextType','string','VariableNamingRule','preserve');
simulators=["xsim","verilator"]; result=struct([]); initialSetRows=struct([]); rareAuditRows=struct([]);
seeds=1401:1410; initSizes=[8,16,32]; countBudgets=[5,10,20,40]; costFractions=[.25,.5,.75,1];
% Validate both simulators' complete label/mask/bin joins before any policy replay.
prepared=struct([]);train=find(split=="train");n=numel(train);b=numel(bins);
for z=1:numel(simulators)
 p=prepareCoverageMask(simulators(z),L,MD,ids(train),bins,reach,reachText);
 prepared=append(prepared,p);
 for j=1:numel(p.rareAuditRows),rareAuditRows=append(rareAuditRows,p.rareAuditRows(j));end
end
writeStruct(fullfile(out,'rare_mask_audit.csv'),rareAuditRows);
for z=1:numel(simulators)
 sim=simulators(z);p=prepared(z);Y=p.Y;V=p.V;usable=p.usable;rare=p.rare;trainMax=p.trainMax;Prob=nan(n,b);obsCost=nan(n,1);predCost=nan(n,1);
 for i=1:n
  id=ids(train(i));
  q=P(string(P.test_id)==id & string(P.simulator)==sim,:); [ok,bi]=ismember(string(q.bin_id),bins);
  Prob(i,bi(ok))=str2double(string(q.calibrated_probability(ok)));
  c=C(string(C.test_id)==id & string(C.simulator)==sim,:); obsCost(i)=str2double(string(c.observed_cycles));
  % Exact candidate key is asserted in the pre-loop cost audit.
  modelLoc=find(string({bundle.costModels.simulator})==sim); selectedModel=string(bundle.costModels(modelLoc).selected_model);
  c=costAudit(string({costAudit.test_id})==id & string({costAudit.simulator})==sim & string({costAudit.split})=="train" & string({costAudit.target})=="observed_cycles" & string({costAudit.selected_model})==selectedModel & string({costAudit.unit})=="cycle");
  if numel(c)~=1||c.match_count~=1||~isfinite(c.predicted_cycles)||c.predicted_cycles<=0,error('Cost join invariant failed for %s/%s.',id,sim);end
  predCost(i)=c.predicted_cycles;
 end
 if any(~isfinite(obsCost)|obsCost<=0)||any(~isfinite(predCost)|predCost<=0),error('Missing/nonpositive cost for %s',sim);end
 for seed=seeds
  rng(seed,'twister'); base=randperm(n,32); % nested, identical initial sets for every paired policy
  for ii=1:numel(base), initialSetRows=append(initialSetRows,struct('simulator',sim,'seed',seed,'initial_rank',ii,'test_id',ids(train(base(ii))),'split',"train",'shared_between_simulator_views',true));end
  for iz=1:numel(initSizes)
   init=base(1:initSizes(iz)); cand=setdiff(1:n,init,'stable'); start=any(V(init,:) & (Y(init,:)==1),1)';
   % Fixed candidate scores use predictions and the initial observed coverage only.
   residual=~start & usable; marginal=sum(Prob(cand,residual),2,'omitnan');
   bytes=str2double(string(F.program_bytes(train(cand)))); uniq=str2double(string(F.unique_byte_values(train(cand))));
   static=bytes+uniq; costScore=marginal./predCost(cand);
   orderRandom=randperm(numel(cand));
   methods=["full_suite","random","static_heuristic","predicted_coverage","cost_aware_predicted","actual_label_oracle_upper_bound"];
   orders={1:numel(cand),orderRandom,rankDesc(static),rankDesc(marginal),rankDesc(costScore),rankDesc(sum(V(cand,residual)&(Y(cand,residual)==1),2))};
   for mi=1:numel(methods)
     ord=orders{mi}; ord=ord(:); % preserve ranking, remove row/column loop ambiguity
    % Both budget families share candidates/initial set. Full suite is a reference curve.
    for bt=1:numel(countBudgets)
      take=reshape(ord(1:min(countBudgets(bt),numel(ord))),1,[]);
     result=addCurve(result,sim,seed,initSizes(iz),methods(mi),"test_count",countBudgets(bt),take,cand,init,Y,V,usable,rare,obsCost,predCost,start,trainMax);
    end
    for bf=1:numel(costFractions)
      budget=costFractions(bf)*sum(predCost(cand));
      [take,used]=selectCostPrefix(ord,cand,predCost(cand),budget,methods(mi),seed);
      if ~isscalar(used)||any(~isfinite(used)),error('Invalid accumulated scalar cost for policy=%s seed=%d.',methods(mi),seed);end
     result=addCurve(result,sim,seed,initSizes(iz),methods(mi),"predicted_cost",budget,take,cand,init,Y,V,usable,rare,obsCost,predCost,start,trainMax);
    end
   end
  end
 end
end
writeStruct(fullfile(out,'partial_replay_curves.csv'),result);
writeStruct(fullfile(out,'initial_sets.csv'),initialSetRows);
% Stage 13 acquired-only replay remains a separate condition and source artifact.
copyfile(fullfile(root,'reports','stage13_active_learning','learning_curves.csv'),fullfile(out,'stage13_training_active_learning_curves.csv'));
% Existing saturated held-out outcomes are explicitly carried as exploratory historical evidence.
copyfile(fullfile(root,'reports','stage12_test_selection','selection_curves.csv'),fullfile(out,'historical_saturated_heldout_curves_exploratory.csv'));
summary=summarizePaired(result); writeStruct(fullfile(out,'paired_summary.csv'),summary);
writeStruct(fullfile(out,'paired_differences.csv'),pairedDifferences(result));
writeStruct(fullfile(out,'auc_summary.csv'),aucSummary(result));
makePlots(out,result);
save(fullfile(out,'stage14_replay.mat'),'result','summary','cfg','-v7.3');
elapsed=toc(batchClock);
writeJson(fullfile(out,'manifest.json'),struct('schema_version','stage14-experiments-1.0.0','configuration_sha256',sha(fullfile(out,'configuration.json')),'cost_join_audit_sha256',sha(fullfile(out,'cost_join_audit.csv')),'rare_mask_audit_sha256',sha(fullfile(out,'rare_mask_audit.csv')),'initial_sets_sha256',sha(fullfile(out,'initial_sets.csv')),'curves_sha256',sha(fullfile(out,'partial_replay_curves.csv')),'paired_summary_sha256',sha(fullfile(out,'paired_summary.csv')),'paired_differences_sha256',sha(fullfile(out,'paired_differences.csv')),'auc_summary_sha256',sha(fullfile(out,'auc_summary.csv')),'runtime',cfg.runtime,'batch_runtime_seconds',elapsed,'conditions_separate',true,'heldout_is_exploratory',true));
validateBatch(root,out);
end

function [take,used]=selectCostPrefix(ordering,cand,candidateCosts,budget,policy,seed)
ordering=ordering(:);candidateCosts=candidateCosts(:);cand=cand(:);
if numel(candidateCosts)~=numel(cand)||numel(ordering)>numel(cand)||any(~isfinite(candidateCosts)|candidateCosts<=0)||~isscalar(budget)||~isfinite(budget)||budget<0
 fprintf(2,'Selection preflight failure: policy=%s seed=%d ordering size=%s jj size=not-iterated cand size=%s predicted-cost size=%s budget=%s\n',policy,seed,mat2str(size(ordering)),mat2str(size(cand)),mat2str(size(candidateCosts)),mat2str(budget));
 error('Selection input dimensions/costs invalid for policy=%s seed=%d: ordering=%s cand=%s predictedCosts=%s budget=%s.',policy,seed,mat2str(size(ordering)),mat2str(size(cand)),mat2str(size(candidateCosts)),mat2str(budget));
end
if any(ordering<1|ordering>numel(cand)|ordering~=floor(ordering))||numel(unique(ordering))~=numel(ordering)
 fprintf(2,'Selection ordering failure: policy=%s seed=%d ordering size=%s jj size=not-iterated cand size=%s predicted-cost size=%s\n',policy,seed,mat2str(size(ordering)),mat2str(size(cand)),mat2str(size(candidateCosts)));
 error('Selection ordering invalid for policy=%s seed=%d.',policy,seed);
end
take=zeros(1,0);used=0;
for orderPos=1:numel(ordering)
 jj=ordering(orderPos);
 if ~isscalar(jj)||jj<1||jj>numel(cand)||jj~=floor(jj)
  fprintf(2,'Selection index failure: policy=%s seed=%d ordering size=%s jj size=%s cand size=%s predicted-cost size=%s\n',policy,seed,mat2str(size(ordering)),mat2str(size(jj)),mat2str(size(cand)),mat2str(size(candidateCosts)));
  error('Policy ordering did not yield one valid candidate index.');
 end
 cost=candidateCosts(jj);
 if ~isscalar(cost)||~isfinite(cost)||cost<=0
  fprintf(2,'Selection cost failure: policy=%s seed=%d ordering size=%s jj=%d jj size=%s cand size=%s predicted-cost size=%s\n',policy,seed,mat2str(size(ordering)),jj,mat2str(size(jj)),mat2str(size(cand)),mat2str(size(candidateCosts)));
  error('Policy candidate did not yield exactly one finite positive predicted cost.');
 end
 if used+cost<=budget,take(end+1)=jj;used=used+cost;end %#ok<AGROW>
end
end

function checkSelectionLoops()
ids=["A";"B";"C"];costs=[2;3;5];order=[3,1,2];budget=7;
[takeR,costR]=selectCostPrefix(order,1:3,costs,budget,"fixture",1);
[takeC,costC]=selectCostPrefix(order(:),(1:3)',costs(:),budget,"fixture",1);
if ~isequal(ids(takeR),ids(takeC))||~isequal(takeR,takeC)||costR~=costC||costR~=7,error('Row/column orientation changed exact-budget selected IDs or cost.');end
[emptyTake,emptyCost]=selectCostPrefix(zeros(1,0),zeros(1,0),zeros(0,1),0,"empty",1);
if ~isempty(emptyTake)||emptyCost~=0,error('Empty-pool selection fixture failed.');end
[oneTake,oneCost]=selectCostPrefix(1,7,4,4,"single",1);
if ~isequal(oneTake,1)||oneCost~=4,error('One-candidate exact-boundary fixture failed.');end
[belowTake,belowCost]=selectCostPrefix([3;1;2],1:3,costs,6.999,"below-boundary",1);
if ~isequal(belowTake,3)||belowCost~=5,error('Strictly below exact-budget boundary fixture failed.');end
fprintf('Focused selection checks passed: row/column equivalence, empty pool, one candidate, exact and below-boundary budgets.\n');
end

function r=addCurve(r,sim,seed,initN,policy,budgetType,budget,take,cand,init,Y,V,usable,rare,obsCost,predCost,start,attainable)
ix=cand(take); covered=start | any(V(ix,:) & (Y(ix,:)==1),1)'; actual=sum(obsCost(ix)); predicted=sum(predCost(ix)); target=unique(max(0,min(1,[.5 .75 .9]))*attainable);
% One row per selected prefix supports curves and explicit target attainability.
for k=0:numel(ix)
 cov=start; if k>0,cov=cov|any(V(ix(1:k),:) & (Y(ix(1:k),:)==1),1)';end
 observed=sum(obsCost(ix(1:k))); if budgetType=="predicted_cost",overrun=max(0,observed-budget);else,overrun=NaN;end
 r=append(r,struct('condition',"partial_training_pool_replay",'simulator',sim,'seed',seed,'initial_count',initN,'candidate_count',numel(cand),'policy',policy,'budget_type',budgetType,'budget',budget,'selected_count',k,'reachable_covered',sum(cov&usable),'reachable_denominator',sum(usable),'rare_retained',sum(cov&rare&usable),'rare_denominator',sum(rare&usable),'predicted_cycles',sum(predCost(ix(1:k))),'observed_cycles_evaluation_only',observed,'observed_budget_overrun',overrun,'oracle_actual_labels',policy=="actual_label_oracle_upper_bound"));
end
% Cost-to-target table rows are emitted in the same machine-readable curve file.
for t=1:numel(target)
 reached=find(arrayfun(@(k) sum((start|any(V(ix(1:k),:) & (Y(ix(1:k),:)==1),1)')&usable)>=target(t),0:numel(ix)),1)-1;
 if isempty(reached), reached=-1; end
 r=append(r,struct('condition',"partial_training_pool_replay",'simulator',sim,'seed',seed,'initial_count',initN,'candidate_count',numel(cand),'policy',policy,'budget_type',budgetType+"_target",'budget',target(t),'selected_count',reached,'reachable_covered',sum(covered&usable),'reachable_denominator',sum(usable),'rare_retained',sum(covered&rare&usable),'rare_denominator',sum(rare&usable),'predicted_cycles',NaN,'observed_cycles_evaluation_only',NaN,'observed_budget_overrun',NaN,'oracle_actual_labels',policy=="actual_label_oracle_upper_bound"));
end
end
function rows=buildTrainingCostJoin(F,ids,split,CP,costModels,pre)
required=["test_id","simulator","split","target","predicted_cycles","unit","selected_model"];
if ~all(ismember(required,string(CP.Properties.VariableNames))),error('Stage 11 cost-prediction schema missing required key/value columns. Present: %s',strjoin(string(CP.Properties.VariableNames),','));end
if any(string(CP.split)~="validation"&string(CP.split)~="test")||any(string(CP.target)~="observed_cycles")||any(string(CP.unit)~="cycle"),error('Stage 11 cost predictions contain unexpected partition/target/unit.');end
cpValues=str2double(string(CP.predicted_cycles));if any(~isfinite(cpValues)|cpValues<=0),error('Stage 11 exported cost predictions contain missing, nonfinite, or nonpositive values.');end
cpKey=joinKey(string(CP.test_id),string(CP.simulator),string(CP.split),string(CP.target),string(CP.selected_model),string(CP.unit));
[~,~,g]=unique(cpKey); cpCounts=accumarray(g,1); cpDup=find(cpCounts>1);
exportDuplicates={};if ~isempty(cpDup),dupKeys=unique(cpKey(cpCounts(g)>1));exportDuplicates=cellstr(dupKeys);fprintf(2,'Duplicate Stage 11 exported complete cost keys:\n');disp(CP(ismember(cpKey,dupKeys),:));end

raw=[str2double(string(F.program_bytes)),str2double(string(F.unique_byte_values))];
cfg=string(F.configuration); levels=string(pre.configuration_levels_from_training);
if size(raw,1)~=numel(ids)||any(~isfinite(raw),'all'),error('Invalid cost predictor rows.');end
X=[(raw-pre.training_mean)./pre.training_scale,double(cfg==levels')];
candidateIds=ids(split=="train"); candidateRows=struct('test_id',{},'simulator',{},'split',{},'target',{},'selected_model',{},'unit',{},'predicted_cycles',{},'prediction_source',{},'source_export_match_count',{},'model_training_scope',{},'candidate_in_model_training_scope',{},'cost_model_fit_seconds',{},'cost_model_inference_seconds',{},'fit_repeated',{}); missing={}; duplicate=exportDuplicates; invalid={};
for sim=["xsim","verilator"]
 modelLoc=find(string({costModels.simulator})==sim);
 if numel(modelLoc)~=1,missing{end+1}=char("selected model for "+sim);continue;end %#ok<AGROW>
 model=costModels(modelLoc).model; selected=string(costModels(modelLoc).selected_model);
 exportRows=string(CP.simulator)==sim;
 if any(string(CP.selected_model(exportRows))~=selected),invalid{end+1}=char("frozen selected_model mismatch for "+sim);end %#ok<AGROW>
 % Print the failing key and schema context (expected train partition).
 if sim=="xsim" && any(candidateIds=="stage5:a_divider")
  failId="stage5:a_divider"; rel=string(CP.test_id)==failId; exact=rel&string(CP.simulator)==sim&string(CP.split)=="train"&string(CP.target)=="observed_cycles"&string(CP.selected_model)==selected&string(CP.unit)=="cycle";
  fprintf('Stage 11 export diagnostic: test_id=%s simulator=%s split=train target=observed_cycles selected_model=%s unit=cycle; matched-row count=%d\n',failId,sim,selected,sum(exact));
  fprintf('Stage 11 cycle_predictions columns: %s\n',strjoin(string(CP.Properties.VariableNames),', '));
  fprintf('Rows for this test_id in Stage 11 cycle_predictions (zero rows is expected for train):\n');disp(CP(rel,:));
 end
 tr=find(split=="train"); inferClock=tic;pred=applyFrozenCost(model,X(tr,:));inferSeconds=toc(inferClock);
 if numel(pred)~=numel(tr),invalid{end+1}=char("prediction count mismatch for "+sim);continue;end %#ok<AGROW>
 for k=1:numel(tr)
  candidateRows=append(candidateRows,struct('test_id',ids(tr(k)),'simulator',sim,'split',"train",'target',"observed_cycles",'selected_model',selected,'unit',"cycle",'predicted_cycles',pred(k),'prediction_source',"frozen_stage11_model_applied_to_train_features",'source_export_match_count',0,'model_training_scope',"train",'candidate_in_model_training_scope',true,'cost_model_fit_seconds',NaN,'cost_model_inference_seconds',inferSeconds,'fit_repeated',false));
 end
end
% Audit every complete candidate key before any experiment-policy loop begins.
keys=joinKey(string({candidateRows.test_id}),string({candidateRows.simulator}),string({candidateRows.split}),string({candidateRows.target}),string({candidateRows.selected_model}),string({candidateRows.unit}));
if ~isempty(keys),[uk,~,ig]=unique(keys); cnt=accumarray(ig,1); duplicate=[duplicate,cellstr(uk(cnt>1))];end %#ok<AGROW>
rows=struct([]);
for k=1:numel(candidateIds)
 for sim=["xsim","verilator"]
  ml=find(string({costModels.simulator})==sim); if numel(ml)==1,expectedModel=string(costModels(ml).selected_model);else,expectedModel="<missing-model>";end
  loc=find(string({candidateRows.test_id})==candidateIds(k)&string({candidateRows.simulator})==sim&string({candidateRows.split})=="train"&string({candidateRows.target})=="observed_cycles"&string({candidateRows.selected_model})==expectedModel&string({candidateRows.unit})=="cycle");
  n=numel(loc); if n==0,missing{end+1}=char(joinKey(candidateIds(k),sim,"train","observed_cycles",expectedModel,"cycle"));continue;elseif n>1,duplicate{end+1}=char(joinKey(candidateIds(k),sim,"train","observed_cycles",expectedModel,"cycle"));continue;end %#ok<AGROW>
  x=candidateRows(loc); if ~isfinite(x.predicted_cycles)||x.predicted_cycles<=0,invalid{end+1}=char(joinKey(x.test_id,x.simulator,x.split,x.target,x.selected_model,x.unit));end %#ok<AGROW>
   rows=append(rows,struct('test_id',x.test_id,'simulator',x.simulator,'split',x.split,'target',x.target,'selected_model',x.selected_model,'unit',x.unit,'predicted_cycles',x.predicted_cycles,'match_count',n,'source_export_match_count',x.source_export_match_count,'prediction_source',x.prediction_source,'model_training_scope',x.model_training_scope,'candidate_in_model_training_scope',x.candidate_in_model_training_scope,'cost_model_fit_seconds',x.cost_model_fit_seconds,'cost_model_inference_seconds',x.cost_model_inference_seconds,'fit_repeated',x.fit_repeated));
 end
end
if ~isempty(missing)||~isempty(duplicate)||~isempty(invalid)
 error('Stage 14 cost-key audit failed before experiment loop. Missing keys [%s]; duplicate keys [%s]; invalid costs [%s].',strjoin(string(missing),'; '),strjoin(string(duplicate),'; '),strjoin(string(invalid),'; '));
end
end
function k=joinKey(id,sim,split,target,model,unit),k=string(id)+"|"+string(sim)+"|"+string(split)+"|"+string(target)+"|"+string(model)+"|"+string(unit);end
function y=applyFrozenCost(c,X)
switch string(c.type)
 case "median",y=repmat(double(c.model),size(X,1),1);
 case "ridge",y=[ones(size(X,1),1),X]*double(c.model);
 case "tree",y=predict(c.model,X);
 otherwise,error('Unsupported frozen Stage 11 cost-model type %s.',string(c.type));
end
y=double(y(:));
end
function p=prepareCoverageMask(sim,L,MD,trainIDs,bins,reach,reachText)
n=numel(trainIDs);b=numel(bins);Y=nan(n,b);V=false(n,b);App=false(n,b);Avail=false(n,b);LabelState=strings(n,b);
for i=1:n
 id=trainIDs(i);q=L(string(L.test_id)==id&string(L.simulator)==sim,:);
 loc=alignBinRows(bins,string(q.bin_id),"coverage labels "+id+"/"+sim);q=q(loc,:);
 a=str2double(string(q.applicable));av=str2double(string(q.available));value=str2double(string(q.value));state=string(q.state);
 [v,y]=validateObservationRows(a,av,value,state,"coverage labels "+id+"/"+sim);
 App(i,:)=a==1;Avail(i,:)=av==1;Y(i,:)=y;V(i,:)=v;LabelState(i,:)=state;
end
if ~isequal(size(Y),[n b])||~isequal(size(V),[n b])||~isequal(size(App),[n b])||~isequal(size(Avail),[n b])||~isequal(size(LabelState),[n b])||any(ismissing(LabelState),'all')||any(LabelState=="",'all')
 error('Coverage matrices are misdimensioned or contain unclassified states (%s).',sim);
end
md=MD(string(MD.simulator)==sim,:);loc=alignBinRows(bins,string(md.bin_id),"Stage 11 rare metrics/"+sim);md=md(loc,:);
sourceImportType=string(class(md.rare_positive));rawRare=numericTableColumn(md.rare_positive,'rare_positive');metaSupport=numericTableColumn(md.train_support,'train_support');metaPositive=numericTableColumn(md.train_positive,'train_positive');
if numel(rawRare)~=b||any(~isfinite(rawRare)|~ismember(rawRare,[0,1]))||any(~isfinite(metaSupport)|metaSupport<0|metaSupport~=floor(metaSupport))||any(~isfinite(metaPositive)|metaPositive<0|metaPositive~=floor(metaPositive))
 error('Stage 11 rare/support values must be finite numeric counts and binary rarity values for %s.',sim);
end
[rareKnown,rare,trainSupport,trainPositive,usable]=deriveRareMask(Y,V,reach);
if any(~isfinite(trainSupport)|~isfinite(trainPositive))||any(trainSupport~=metaSupport)||any(trainPositive~=metaPositive)
 bad=(trainSupport~=metaSupport)|(trainPositive~=metaPositive);fprintf(2,'Stage 10 versus Stage 11 training support mismatch (%s):\n',sim);disp(table(bins(bad),trainSupport(bad),metaSupport(bad),trainPositive(bad),metaPositive(bad),'VariableNames',{'bin_id','derived_support','stage11_support','derived_positive','stage11_positive'}));error('Frozen training support alignment failed for %s.',sim);
end
metadataRare=double(trainPositive<5);metadataMismatch=rareKnown&(rawRare~=metadataRare);
if any(metadataMismatch),fprintf(2,'Stage 11 rare_positive differs from train-only positive_count<5 (%s):\n',sim);disp(table(bins(metadataMismatch),rawRare(metadataMismatch),trainSupport(metadataMismatch),trainPositive(metadataMismatch),'VariableNames',{'bin_id','stage11_rare_positive','train_support','train_positive'}));error('Rarity definition mismatch for %s.',sim);end
if any(~isfinite(trainSupport)|~isfinite(trainPositive))||any(trainSupport<0)||any(trainPositive<0|trainPositive>trainSupport)||any(~ismember(reach,[false true]))||any(~ismember(usable,[false true]))||any(~ismember(rare,[false true]))
 error('Reachability, support, or rarity mask contains invalid dimensions/values (%s).',sim);
end
hits=V&(Y==1);trainMax=sum(usable&any(hits,1)');
% Reproduce the obsolete logical-to-number cast per bin for audit only.
% `str2double(logicalVector)` can scalar-expand/return an unexpected shape;
% never index that result as though it were aligned with dictionary bins.
legacyComparison=rawRare==1;legacy=nan(size(rawRare));legacyFailure=false(size(rawRare));
for k=1:numel(rawRare)
 try
  converted=str2double(legacyComparison(k));
  if isscalar(converted),legacy(k)=converted;else,legacyFailure(k)=true;end
 catch
  legacyFailure(k)=true;
 end
end
perBin={'rawRare','legacyComparison','legacy','legacyFailure','bins','reachText','trainSupport','trainPositive','rareKnown','metadataRare','metadataMismatch','reach','rare','usable'};
for k=1:numel(perBin),v=eval(perBin{k});fprintf('MASK_AUDIT_SHAPE %s %s size=%s numel=%d\n',perBin{k},class(v),mat2str(size(v)),numel(v));if numel(v)~=b,error('Per-bin audit field %s is misaligned: expected %d values, got size %s.',perBin{k},b,mat2str(size(v)));end,end
if ~isequal(size(rawRare),size(legacyComparison),size(legacy),size(bins)),error('Legacy audit vectors do not share the dictionary bin shape.');end
badCast=~isfinite(legacy);
fprintf('RARE_MASK %s: bins=%d, reachable=%d, train-supported=%d, support-unknown=%d, rare=%d, old-cast-NaNs=%d\n',sim,b,sum(reach),sum(rareKnown),sum(~rareKnown),sum(rare),sum(badCast));
if any(badCast),fprintf('Old-cast offending bin IDs and original values (%s): %s\n',sim,strjoin(bins(badCast)+"="+string(rawRare(badCast)),', '));end
audit=struct([]);
for j=1:b
 audit=append(audit,struct('simulator',sim,'bin_id',bins(j),'source_import_type',sourceImportType,'stage11_rare_positive_original',rawRare(j),'legacy_comparison_result',legacyComparison(j),'legacy_str2double_result',legacy(j),'legacy_conversion_failed',legacyFailure(j),'reachability',reachText(j),'train_support_observed',trainSupport(j),'train_positive_observed',trainPositive(j),'rare_known',rareKnown(j),'rare_by_train_positive_lt_5',rare(j),'train_constant_known',rareKnown(j)&(trainPositive(j)==0|trainPositive(j)==trainSupport(j)),'train_applicable_count',sum(App(:,j)),'train_available_count',sum(Avail(:,j)),'train_evidence_count',sum(V(:,j)),'train_observed_zero_count',sum(LabelState(:,j)=="observed_zero"),'train_observed_hit_count',sum(LabelState(:,j)=="observed_hit"),'train_inapplicable_count',sum(LabelState(:,j)=="inapplicable"),'train_unavailable_count',sum(LabelState(:,j)=="unavailable"),'train_unsupported_count',sum(LabelState(:,j)=="unsupported")));
end
if numel(audit)~=b||~isequal(string({audit.bin_id})',bins),error('Per-bin audit export row ordering/count does not match the frozen dictionary (%s).',sim);end
fprintf('  State audit example rows (original rarity, reach, applicability/availability states):\n');disp(struct2table(audit(1:min(12,b))));
p=struct('simulator',sim,'Y',Y,'V',V,'App',App,'Avail',Avail,'LabelState',LabelState,'trainSupport',trainSupport,'trainPositive',trainPositive,'rareKnown',rareKnown,'usable',usable,'rare',rare,'trainMax',trainMax,'rareAuditRows',audit);
end
function checkMaskAudit(root,out)
checkDictionary(root);
d=fullfile(root,'reports','stage10_dataset');m=jsondecode(fileread(fullfile(d,'manifest.json')));names=fieldnames(m.csv_outputs);
for k=1:numel(names),fn=strrep(names{k},'_csv','.csv');p=fullfile(d,fn);if ~isfile(p)||~strcmpi(sha(p),m.csv_outputs.(names{k}).sha256),error('Stage 10 frozen input hash mismatch: %s',fn);end,end
F=readtable(fullfile(d,'features.csv'),'TextType','string','VariableNamingRule','preserve');S=readtable(fullfile(d,'split_assignments.csv'),'TextType','string','VariableNamingRule','preserve');
L=readtable(fullfile(d,'coverage_labels.csv'),'TextType','string','VariableNamingRule','preserve');D=readtable(fullfile(d,'bin_dictionary.csv'),'TextType','string','VariableNamingRule','preserve');
MD=readtable(fullfile(root,'reports','stage11_matlab_ml','metrics_per_bin.csv'),'TextType','string','VariableNamingRule','preserve');
[bins,reachText,reach]=validateDictionary(D);[ok,loc]=ismember(string(F.test_id),string(S.test_id));if ~all(ok),error('Frozen split IDs fail during focused mask audit.');end
trainIDs=string(F.test_id(string(S.split(loc))=="train"));if numel(trainIDs)~=196,error('Focused mask audit requires exactly 196 frozen training IDs.');end
allRows=struct([]);for sim=["xsim","verilator"]
 p=prepareCoverageMask(sim,L,MD,trainIDs,bins,reach,reachText);
 if numel(p.rareAuditRows)~=316||numel(unique(string({p.rareAuditRows.bin_id})))~=316,error('Per-simulator audit rows are incomplete or duplicated (%s).',sim);end
 for j=1:numel(p.rareAuditRows),allRows=append(allRows,p.rareAuditRows(j));end
end
if numel(allRows)~=632,error('Combined audit must contain 632 simulator/bin rows.');end
diagDir=fullfile(out,'diagnostics');if ~isfolder(diagDir),mkdir(diagDir);end
auditPath=fullfile(diagDir,'rare_mask_audit_focused_check.csv');writeStruct(auditPath,allRows);
R=readtable(auditPath,'TextType','string','VariableNamingRule','preserve');key=string(R.simulator)+"|"+string(R.bin_id);
expectedRare=(R.rare_known>0)&(R.reachability=="reachable")&(R.train_positive_observed<5);
if height(R)~=632||numel(unique(key))~=632||any((R.rare_by_train_positive_lt_5>0)~=expectedRare),error('Exported focused audit CSV failed row/key/mask consistency checks.');end
fprintf('Focused two-simulator 316-bin audit passed and exported: %s (rows=%d, denominator=%d).\n',auditPath,height(R),sum(reach));
end
function loc=alignBinRows(expected,provided,context)
expected=string(expected(:));provided=string(provided(:));
if numel(provided)~=numel(expected)||numel(unique(provided))~=numel(provided)||any(ismissing(provided))
 error('Bin row count/uniqueness failure for %s (expected=%d, provided=%d).',context,numel(expected),numel(provided));
end
[ok,loc]=ismember(expected,provided);if ~all(ok)||numel(unique(loc))~=numel(expected)
 error('Bin-ID alignment failure for %s; missing IDs: %s; extra IDs: %s.',context,strjoin(expected(~ok),', '),strjoin(setdiff(provided,expected),', '));
end
end
function [observed,y]=validateObservationRows(a,av,value,state,context)
a=double(a(:));av=double(av(:));value=double(value(:));state=string(state(:));
if numel(a)~=numel(av)||numel(a)~=numel(value)||numel(a)~=numel(state)||any(~isfinite(a)|~ismember(a,[0,1]))||any(~isfinite(av)|~ismember(av,[0,1]))||any(ismissing(state)|state=="")
 error('Applicability/availability/state fields are missing or nonbinary for %s.',context);
end
validUnsupported=(a==0&av==0&state=="unsupported"&isnan(value));
validInapplicable=(a==0&av==0&state=="inapplicable"&isnan(value));
validUnavailable=(a==1&av==0&state=="unavailable"&isnan(value));
validZero=(a==1&av==1&state=="observed_zero"&isfinite(value)&value==0);
validHit=(a==1&av==1&state=="observed_hit"&isfinite(value)&value==1);
good=validUnsupported|validInapplicable|validUnavailable|validZero|validHit;
if any(~good)
 bad=find(~good);fprintf(2,'Invalid observation rows for %s; row indices: %s\n',context,mat2str(bad(:)'));disp(table(a(bad),av(bad),value(bad),state(bad),'VariableNames',{'applicable','available','value','state'}));error('Observation state/value invariants failed for %s.',context);
end
observed=validZero|validHit;y=nan(size(value));y(observed)=value(observed);
end
function y=numericTableColumn(x,name)
if isnumeric(x),y=double(x(:));elseif isstring(x)||iscellstr(x),y=str2double(string(x(:)));else,error('Unexpected MATLAB import type for %s: %s.',name,class(x));end
end
function checkDictionary(root)
d=fullfile(root,'reports','stage10_dataset');m=jsondecode(fileread(fullfile(d,'manifest.json')));
expected=m.csv_outputs.bin_dictionary_csv.sha256;actual=sha(fullfile(d,'bin_dictionary.csv'));
if ~strcmpi(expected,actual),error('Frozen dictionary hash mismatch: expected %s actual %s.',expected,actual);end
D=readtable(fullfile(d,'bin_dictionary.csv'),'TextType','string','VariableNamingRule','preserve');
[bins,reachText,reach]=validateDictionary(D); %#ok<ASGLU>
categoryValues=unique(reachText,'stable');categoryCounts=arrayfun(@(x)sum(reachText==x),categoryValues);
fprintf('Frozen dictionary categories: %s\n',strjoin(categoryValues+"="+string(categoryCounts),', '));
if height(D)~=316||sum(reach)~=277||sum(~reach)~=39,error('Frozen dictionary denominator assertion failed: expected 316 total = 277 reachable targeted + 39 excluded.');end
L=readtable(fullfile(d,'coverage_labels.csv'),'TextType','string','VariableNamingRule','preserve');
MD=readtable(fullfile(root,'reports','stage11_matlab_ml','metrics_per_bin.csv'),'TextType','string','VariableNamingRule','preserve');
for sim=["xsim","verilator"]
 q=L(string(L.simulator)==sim,:);auditDictionaryAlignment(bins,string(q.bin_id),"Stage 10 coverage_labels/"+sim,316,true);
 q=MD(string(MD.simulator)==sim,:);auditDictionaryAlignment(bins,string(q.bin_id),"Stage 11 metrics_per_bin/"+sim,316,false);
end
validateMaskFixtures();
fprintf('Dictionary focused checks passed against frozen CSV. imported bin_id=%s, reachability=%s; denominator=%d; reachable=%d; unsupported classifications preserved.\n',class(D.bin_id),class(D.reachability),height(D),sum(reach));
end
function [bins,reachText,reach]=validateDictionary(D,expectedCount)
if nargin<2,expectedCount=316;end
if ~ismember('bin_id',D.Properties.VariableNames)||~ismember('reachability',D.Properties.VariableNames)
 fprintf(2,'Dictionary columns missing; imported table columns: %s\n',strjoin(string(D.Properties.VariableNames),', '));error('Frozen dictionary schema is missing required columns.');
end
rawID=D.bin_id;rawReach=D.reachability;bins=string(rawID(:));reachText=string(rawReach(:));
fprintf('Stage 10 dictionary import: rows=%d bin_id MATLAB type=%s reachability MATLAB type=%s\n',height(D),class(rawID),class(rawReach));
missingID=ismissing(bins)|strlength(strtrim(bins))==0;
if any(missingID),fprintf(2,'Missing dictionary bin IDs; rows/raw values/type/condition:\n');disp(table(find(missingID),bins(missingID),repmat(string(class(rawID)),sum(missingID),1),repmat("missing/empty ID",sum(missingID),1),'VariableNames',{'row','raw_bin_id','MATLAB_type','failed_condition'}));error('Dictionary contains missing bin IDs.');end
[u,~,ic]=unique(bins);counts=accumarray(ic,1);dup=u(counts>1);
if ~isempty(dup),ix=find(ismember(bins,dup));fprintf(2,'Duplicate dictionary IDs; rows/raw values/type/condition:\n');disp(table(ix,bins(ix),reachText(ix),repmat(string(class(rawID)),numel(ix),1),repmat(string(class(rawReach)),numel(ix),1),repmat("duplicate bin_id",numel(ix),1),'VariableNames',{'row','raw_bin_id','raw_reachability','bin_id_type','reachability_type','failed_condition'}));error('Dictionary contains duplicate bin IDs.');end
categories=["reachable","unreachable","unsupported","not_targeted"];
badReach=ismissing(reachText)|~ismember(reachText,categories);
if any(badReach),ix=find(badReach);fprintf(2,'Invalid dictionary reachability; rows/raw values/type/condition:\n');disp(table(ix,bins(ix),reachText(ix),repmat(string(class(rawReach)),numel(ix),1),repmat("expected one of: reachable|unreachable|unsupported|not_targeted",numel(ix),1),'VariableNames',{'row','bin_id','raw_reachability','MATLAB_type','failed_condition'}));error('Dictionary contains invalid reachability values.');end
if height(D)~=expectedCount,fprintf(2,'Dictionary row/bin alignment failure: rows=%d expected=%d; IDs=%d; imported types bin_id=%s reachability=%s\n',height(D),expectedCount,numel(unique(bins)),class(rawID),class(rawReach));disp(table((1:height(D))',bins,reachText,'VariableNames',{'row','raw_bin_id','raw_reachability'}));error('Frozen dictionary row/bin alignment failed.');end
reach=reachText=="reachable"; % Only explicitly reachable targeted bins enter coverage denominators.
end
function auditDictionaryAlignment(expected,provided,context,expectedRows,allowRepeated)
provided=provided(:);uProvided=unique(provided);missing=~ismember(expected,uProvided);extra=~ismember(provided,expected);
dupNames=unique(provided);dupCounts=arrayfun(@(x)sum(provided==x),dupNames);dups=dupNames(dupCounts>1);
rowBad=(~allowRepeated&&numel(provided)~=expectedRows)||(allowRepeated&&(mod(numel(provided),expectedRows)~=0||numel(uProvided)~=expectedRows));
dupBad=~allowRepeated&&~isempty(dups);
if rowBad||any(missing)||any(extra)||dupBad
 fprintf(2,'Dictionary/mask alignment failed for %s: rows=%d unique_bins=%d expected_bins=%d missing=%d extra=%d duplicate_bin_rows=%d (repeated allowed=%d)\n',context,numel(provided),numel(uProvided),expectedRows,sum(missing),sum(extra),numel(dups),allowRepeated);
 if any(missing),fprintf(2,'Missing expected bin IDs: %s\n',strjoin(expected(missing),', '));end
 if any(extra),fprintf(2,'Extra raw bin IDs: %s\n',strjoin(unique(provided(extra)),', '));end
 if dupBad,fprintf(2,'Duplicate raw bin IDs: %s\n',strjoin(dups,', '));end
 error('Dictionary/mask row/bin alignment failed for %s.',context);
end
end
function validateMaskFixtures()
% Every producer-supported category remains distinct; only reachable is evaluable.
cats=["reachable";"unreachable";"unsupported";"not_targeted"];
fixtureD=table(("fixture"+string(1:4))',cats,'VariableNames',{'bin_id','reachability'});
[fixtureIDs,fixtureCats,fixtureReach]=validateDictionary(fixtureD,4); %#ok<ASGLU>
if ~isequal(fixtureCats,cats)||~isequal(fixtureReach,[true;false;false;false])||sum(fixtureReach)~=1,error('Reachability category/denominator fixture failed.');end
% Missing/unavailable and unsupported stay unknown; observed zero is false data.
a=[1;0;1;1];av=[0;0;1;1];v=[NaN;NaN;0;1];st=["unavailable";"unsupported";"observed_zero";"observed_hit"];
[obs,y]=validateObservationRows(a,av,v,st,"mask fixture");
if ~isequal(obs,[false;false;true;true])||~isnan(y(1))||~isnan(y(2))||y(3)~=0||y(4)~=1,error('Missing/unsupported/zero/hit mask fixture failed.');end
Y=[zeros(5,1),ones(5,1),nan(5,1)];V=[true(5,2),false(5,1)];[known,rare,support,pos,usable]=deriveRareMask(Y,V,[true;true;true]);
if ~isequal(known,[true;true;false])||~isequal(rare,[true;false;false])||~isequal(support,[5;5;0])||~isequal(pos,[0;5;0])||~isequal(usable,[true;true;false]),error('Constant-bin/strict rare-threshold/missing-support fixture failed.');end
loc=alignBinRows(["b1";"b2"],["b2";"b1"],"misaligned-bin fixture");if ~isequal(loc,[2;1]),error('Misaligned-bin reorder fixture failed.');end
badCaught=false;try,alignBinRows(["b1";"b2"],["b1";"b1"],"duplicate-bin fixture");catch,badCaught=true;end;if ~badCaught,error('Duplicate/missing-bin fixture was not rejected.');end
end
function [known,rare,support,positive,usable]=deriveRareMask(Y,V,reach)
if ~isequal(size(Y),size(V))||size(Y,2)~=numel(reach),error('Rare-mask input dimensions do not align.');end
if any(V&(~isfinite(Y)|~ismember(Y,[0,1])),'all')||any(~V&~isnan(Y),'all')||any(~ismember(reach(:),[false true])),error('Observed labels must be finite binary; unobserved labels must remain NaN; reach must be binary.');end
support=sum(V,1)';positive=sum(V&(Y==1),1)';known=support>0;usable=logical(reach(:))&known;rare=false(size(support));rare(known)=positive(known)<5;rare=rare&usable;
end
function s=summarizePaired(r)
% Summaries preserve seed as the replication unit and policy deltas paired by condition.
if isempty(r),s=struct([]);return;end
keys=unique(string({r.policy})); s=struct([]);
for p=keys
 q=r(string({r.policy})==p & string({r.budget_type})=="test_count" & [r.selected_count]>0 & [r.selected_count]==[r.budget]);
 if isempty(q),continue;end
 s=append(s,struct('policy',p,'condition',"partial_training_pool_replay",'rows',numel(q),'seed_count',numel(unique([q.seed])),'mean_covered_bins',mean([q.reachable_covered]),'std_covered_bins',std([q.reachable_covered]),'mean_observed_cycles',mean([q.observed_cycles_evaluation_only]),'mean_predicted_cycles',mean([q.predicted_cycles]),'mean_overrun_cycles',mean([q.observed_budget_overrun])));
end
end
function d=pairedDifferences(r)
d=struct([]); if isempty(r),return;end
for sim=unique(string({r.simulator})), for init=unique([r.initial_count]), for budget=unique([r.budget]),
 q=r(string({r.simulator})==sim & [r.initial_count]==init & [r.budget]==budget & string({r.budget_type})=="test_count" & [r.selected_count]==[r.budget]);
 for seed=unique([q.seed]), z=q([q.seed]==seed); base=z(string({z.policy})=="random"); if isempty(base),continue;end
 for k=1:numel(z), if z(k).policy=="random",continue;end
 d=append(d,struct('condition',"partial_training_pool_replay",'simulator',sim,'seed',seed,'initial_count',init,'count_budget',budget,'policy',z(k).policy,'paired_delta_reachable_bins_vs_random',z(k).reachable_covered-base(1).reachable_covered,'paired_delta_observed_cycles_vs_random',z(k).observed_cycles_evaluation_only-base(1).observed_cycles_evaluation_only));
 end
 end
end,end,end
end
function a=aucSummary(r)
a=struct([]); if isempty(r),return;end
for p=unique(string({r.policy})), for sim=unique(string({r.simulator})), for init=unique([r.initial_count]),
 q=r(string({r.policy})==p & string({r.simulator})==sim & [r.initial_count]==init & string({r.budget_type})=="test_count" & [r.budget]==40);
 for seed=unique([q.seed]), z=q([q.seed]==seed); [~,u]=unique([z.selected_count],'stable'); z=z(u); [x,o]=sort([z.selected_count]); y=[z(o).reachable_covered]./[z(o).reachable_denominator]; if numel(x)>1, ac=trapz(x,y)/max(x); else, ac=NaN;end
 a=append(a,struct('condition',"partial_training_pool_replay",'simulator',sim,'policy',p,'seed',seed,'initial_count',init,'budget_axis',"selected_test_count",'normalized_auc',ac,'denominator','per-simulator reachable bins'));
 z=q([q.seed]==seed & string({q.budget_type})=="test_count" & [q.budget]==40); [~,u]=unique([z.selected_count],'stable');z=z(u);[x,o]=sort([z.observed_cycles_evaluation_only]);y=[z(o).reachable_covered]./[z(o).reachable_denominator];if numel(x)>1&&max(x)>0,ac=trapz(x,y)/max(x);else,ac=NaN;end
 a=append(a,struct('condition',"partial_training_pool_replay",'simulator',sim,'policy',p,'seed',seed,'initial_count',init,'budget_axis',"observed_execution_cycles_evaluation_only",'normalized_auc',ac,'denominator','per-simulator reachable bins; cycles are simulated units'));
 end
end,end,end
end
function makePlots(out,r)
f=figure('Visible','off'); cleanup=onCleanup(@()close(f)); hold on; policies=unique(string({r.policy}));
for p=policies
 q=r(string({r.policy})==p & string({r.budget_type})=="test_count" & [r.selected_count]>0 & [r.initial_count]==16 & [r.simulator]=="xsim");
 if isempty(q),continue;end
 x=unique([q.selected_count]); y=arrayfun(@(v)mean([q([q.selected_count]==v).reachable_covered]),x); plot(x,y,'-o','DisplayName',char(p));
end
xlabel('Selected tests (count)'); ylabel('Reachable bins covered (denominator: per-simulator training reachable bins)'); title('Stage 14 partial-coverage replay, XSim, initial n=16, 10 seeds; seed mean'); legend('Location','best'); grid on;
exportgraphics(f,fullfile(out,'partial_coverage_xsim.png'),'Resolution',300);
f2=figure('Visible','off'); c2=onCleanup(@()close(f2)); hold on;
for p=policies
 q=r(string({r.policy})==p & string({r.budget_type})=="test_count" & [r.budget]==40 & [r.initial_count]==16 & [r.simulator]=="xsim");
 if isempty(q),continue;end
 x=unique([q.observed_cycles_evaluation_only]); y=arrayfun(@(v)mean([q([q.observed_cycles_evaluation_only]==v).reachable_covered]),x); plot(x,y,'-o','DisplayName',char(p));
end
xlabel('Observed simulated execution cycles (cycles; evaluation only)'); ylabel('Reachable bins covered (denominator: per-simulator training reachable bins)'); title('Stage 14 partial-coverage replay, XSim, initial n=16, 40-test order, 10 seeds; seed mean'); legend('Location','best'); grid on;
exportgraphics(f2,fullfile(out,'partial_coverage_cost_xsim.png'),'Resolution',300);
end
function validateBatch(root,out)
validateMaskFixtures();
req={'configuration.json','manifest.json','cost_join_audit.csv','rare_mask_audit.csv','initial_sets.csv','partial_replay_curves.csv','paired_summary.csv','paired_differences.csv','auc_summary.csv','stage13_training_active_learning_curves.csv','historical_saturated_heldout_curves_exploratory.csv','partial_coverage_xsim.png','partial_coverage_cost_xsim.png','stage14_replay.mat'};
for k=1:numel(req),if ~isfile(fullfile(out,req{k})),error('Missing Stage 14 artifact %s',req{k});end,end
c=jsondecode(fileread(fullfile(out,'configuration.json')));if ~strcmp(c.schema_version,'stage14-experiments-1.0.0')||numel(c.input_hashes)~=16,error('Config/hash validation failed.');end
for k=1:numel(c.input_hashes),if ~strcmpi(c.input_hashes(k).sha256,sha(fullfile(root,strrep(c.input_hashes(k).path,'/',filesep)))),error('Input hash changed: %s',c.input_hashes(k).path);end,end
T=readtable(fullfile(out,'partial_replay_curves.csv'),'TextType','string');
if any(T.reachable_covered>T.reachable_denominator)||any(T.rare_retained>T.rare_denominator)||any(T.selected_count < -1),error('Metric bounds/target markers invalid.');end
if ~any(T.oracle_actual_labels),error('Actual-label oracle must be labeled separately.');end
if ~any(T.condition=="partial_training_pool_replay"),error('Partial condition missing.');end
R=readtable(fullfile(out,'rare_mask_audit.csv'),'TextType','string','VariableNamingRule','preserve');
if height(R)~=632||numel(unique(string(R.simulator)+"|"+string(R.bin_id)))~=632,error('Rare audit dimensions/order keys do not cover both simulator/bin sets.');end
if any(R.source_import_type~="double")||any(~isfinite(R.stage11_rare_positive_original)|~ismember(R.stage11_rare_positive_original,[0,1]))||any(~isfinite(R.train_support_observed)|R.train_support_observed<0)||any(~isfinite(R.train_positive_observed)|R.train_positive_observed<0|R.train_positive_observed>R.train_support_observed),error('Rare audit source/support values are invalid.');end
known=R.train_support_observed>0; reachR=R.reachability=="reachable"; expectedRare=known&reachR&(R.train_positive_observed<5);
if any(double(R.rare_known)~=double(known))||any(double(R.rare_by_train_positive_lt_5)~=double(expectedRare)),error('Rare mask differs from train-only positive_count<5 definition.');end
stateTotal=R.train_observed_zero_count+R.train_observed_hit_count+R.train_inapplicable_count+R.train_unavailable_count+R.train_unsupported_count;
if any(stateTotal~=196)||any(R.train_evidence_count~=R.train_observed_zero_count+R.train_observed_hit_count)||any(R.train_available_count~=R.train_evidence_count)||any(R.train_applicable_count~=R.train_evidence_count+R.train_unavailable_count),error('Rare audit applicability/availability/state accounting is inconsistent.');end
I=readtable(fullfile(out,'initial_sets.csv'),'TextType','string'); if any(I.split~="train"),error('Initial set crosses split.');end
if height(I)~=2*10*32,error('Paired seed initial sets are incomplete.');end
for seed=1401:1410, for rank=1:32,a=I(string(I.simulator)=="xsim"&I.seed==seed&I.initial_rank==rank,:);b=I(string(I.simulator)=="verilator"&I.seed==seed&I.initial_rank==rank,:);if height(a)~=1||height(b)~=1||a.test_id~=b.test_id,error('Paired initial set mismatch.');end,end,end
J=readtable(fullfile(out,'cost_join_audit.csv'),'TextType','string','VariableNamingRule','preserve');
if height(J)~=392||any(J.match_count~=1)||any(~isfinite(J.predicted_cycles)|J.predicted_cycles<=0),error('Candidate cost join has missing, duplicate, or invalid predictions.');end
jkey=joinKey(string(J.test_id),string(J.simulator),string(J.split),string(J.target),string(J.selected_model),string(J.unit));if numel(unique(jkey))~=height(J),error('Duplicate complete candidate cost keys.');end
M=jsondecode(fileread(fullfile(out,'manifest.json'))); if ~strcmpi(M.curves_sha256,sha(fullfile(out,'partial_replay_curves.csv')))||~strcmpi(M.rare_mask_audit_sha256,sha(fullfile(out,'rare_mask_audit.csv'))),error('Export manifest mismatch.');end
% Hand-checkable metric example and deterministic seed schedule guard.
if abs(trapz([0 1],[0 1])-.5)>eps,error('AUC hand-check failed.');end
rng(1401,'twister'); a=randperm(196,32);rng(1401,'twister');b=randperm(196,32);if ~isequal(a,b),error('Seed replay is not deterministic.');end
fprintf('STAGE14 STANDALONE VALIDATION PASS; MATLAB %s\n',version('-release'));
end
function r=append(r,x),if isempty(r),r=x;else,r(end+1)=x;end,end
function o=rankDesc(x),[~,o]=sort(x,'descend','MissingPlacement','last');end
function h=sha(p)
% Match the Stage 13 portable-text convention used by the frozen manifests:
% CSV/JSON/text hashes are over UTF-8 bytes after CRLF/CR -> LF normalization.
[~,~,ext]=fileparts(p);
if any(strcmpi(ext,{'.csv','.json','.txt','.m','.bat','.md'}))
 s=fileread(p);s=strrep(s,sprintf('\r\n'),sprintf('\n'));s=strrep(s,sprintf('\r'),sprintf('\n'));bytes=uint8(unicode2native(s,'UTF-8'));
else
 f=fopen(p,'rb');if f<0,error('Cannot read %s',p);end;c=onCleanup(@()fclose(f));bytes=fread(f,Inf,'*uint8');
end
md=java.security.MessageDigest.getInstance('SHA-256');md.update(bytes);h=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
function verifyStage11Outputs(root,m)
dir11=fullfile(root,'reports','stage11_matlab_ml');
keys={'cycle_predictions_csv','cycle_cost_metrics_csv','predictions_csv','metrics_per_bin_csv','models_mat'};
for k=1:numel(keys)
 key=keys{k};if ~isfield(m.output_files,key),error('Stage 11 manifest lacks frozen artifact %s.',key);end
 rel=m.output_files.(key).path;p=fullfile(dir11,rel);if ~isfile(p)||~strcmpi(shaRaw(p),m.output_files.(key).sha256),error('Stage 11 frozen output raw hash mismatch: %s',rel);end
end
end
function h=shaRaw(p)
 f=fopen(p,'rb');if f<0,error('Cannot read %s',p);end;c=onCleanup(@()fclose(f));b=fread(f,Inf,'*uint8');md=java.security.MessageDigest.getInstance('SHA-256');md.update(b);h=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
function writeStruct(p,x),if isempty(x),writetable(table(),p);else,writetable(struct2table(x),p);end,end
function writeJson(p,x),f=fopen(p,'w');c=onCleanup(@()fclose(f));fwrite(f,jsonencode(x,'PrettyPrint',true),'char');fwrite(f,newline,'char');end
