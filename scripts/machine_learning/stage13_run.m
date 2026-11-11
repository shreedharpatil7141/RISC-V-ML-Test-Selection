function stage13_run(mode)
% Offline Stage 13 replay. No simulator is executed and no live hardware is queried.
if nargin<1, mode="run"; end
root=pwd; outDir=fullfile(root,'reports','stage13_active_learning');
if string(mode)=="run", runStage13(root,outDir); else, validateStage13(root,outDir); end
end

function [F,S,L,D,C,bins,hashes]=loadStageData(root)
d=fullfile(root,'reports','stage10_dataset'); m=jsondecode(fileread(fullfile(d,'manifest.json')));
if m.schema_version~="stage10-dataset-1.0.0" || m.logical_tests~=282 || ...
        m.split_counts.train~=196 || m.split_counts.validation~=46 || m.split_counts.test~=40
    error('Stage 10 frozen schema/split invalid.');
end
if m.source_closure_status.provenance~="PASS"||m.source_closure_status.xsim~="CLOSED"||m.source_closure_status.verilator~="CLOSED"||numel(fieldnames(m.csv_outputs))~=10,error('Stage 10 closure or dictionary manifest invalid.');end
hashes=struct('path',{},'sha256',{}); names=fieldnames(m.csv_outputs);
for k=1:numel(names)
 filename=strrep(names{k},'_csv','.csv'); p=fullfile(d,filename); if ~isfile(p)||~strcmpi(shaText(p),m.csv_outputs.(names{k}).sha256), error('Stage 10 hash mismatch: %s',filename); end
 hashes(end+1)=struct('path',"reports/stage10_dataset/"+filename,'sha256',m.csv_outputs.(names{k}).sha256); %#ok<AGROW>
end
F=readtable(fullfile(d,'features.csv'),'TextType','string','VariableNamingRule','preserve');
S=readtable(fullfile(d,'split_assignments.csv'),'TextType','string','VariableNamingRule','preserve');
L=readtable(fullfile(d,'coverage_labels.csv'),'TextType','string','VariableNamingRule','preserve');
D=readtable(fullfile(d,'bin_dictionary.csv'),'TextType','string','VariableNamingRule','preserve');
C=readtable(fullfile(d,'execution_costs.csv'),'TextType','string','VariableNamingRule','preserve'); bins=string(D.bin_id);
% Validate upstream artifact lineage; Stage 11 weights are provenance only.
s11=fullfile(root,'reports','stage11_matlab_ml'); s11m=jsondecode(fileread(fullfile(s11,'manifest.json')));
if s11m.schema_version~="stage11-matlab-ml-1.0.0"||s11m.base_commit~="2d195e581075c1a4cb7bb17d172d22a7472a8a9b",error('Stage 11 lineage invalid.');end
mh=shaPortable(fullfile(s11,'models.mat'));if ~strcmpi(mh,s11m.output_files.models_mat.sha256),error('Frozen Stage 11 model hash changed.');end
rh=shaRawFile(fullfile(s11,'metrics_per_bin.csv'));if ~strcmpi(rh,s11m.output_files.metrics_per_bin_csv.sha256),error('Stage 11 rare-bin dictionary hash changed.');end
s12=fullfile(root,'reports','stage12_test_selection');s12m=jsondecode(fileread(fullfile(s12,'manifest.json')));
if s12m.schema_version~="stage12-selection-1.0.0"||s12m.base_commit~="b0856cc6f7e954908f266ee0bf31299542aec3c2",error('Stage 12 policy lineage invalid.');end
ph=shaPortable(fullfile(s12,'policy_choices.csv'));if ~strcmpi(ph,s12m.output_files.policy_choices_csv.sha256),error('Frozen Stage 12 policy hash changed.');end
hashes(end+1)=struct('path',"reports/stage11_matlab_ml/models.mat",'sha256',mh); %#ok<AGROW>
hashes(end+1)=struct('path',"reports/stage11_matlab_ml/metrics_per_bin.csv",'sha256',rh); %#ok<AGROW>
hashes(end+1)=struct('path',"reports/stage11_matlab_ml/manifest.json",'sha256',shaPortable(fullfile(s11,'manifest.json'))); %#ok<AGROW>
hashes(end+1)=struct('path',"reports/stage12_test_selection/policy_choices.csv",'sha256',ph); %#ok<AGROW>
hashes(end+1)=struct('path',"reports/stage12_test_selection/manifest.json",'sha256',shaPortable(fullfile(s12,'manifest.json'))); %#ok<AGROW>
if height(F)~=282||height(S)~=282||height(L)~=178224||height(C)~=564||numel(unique(string(F.test_id)))~=282
 error('Stage 10 row counts or logical IDs invalid.'); end
if ~all(ismember(string(L.simulator),["xsim","verilator"]))||any(string(L.observation_id)==""),error('Stage 10 provenance invalid.');end
end
function x=buildSimulator(sim,F,ids,split,groups,L,D,C,bins)
n=numel(ids); b=numel(bins); T=L(string(L.simulator)==sim,:); Y=NaN(n,b); app=false(n,b); av=false(n,b); state=repmat("unavailable",n,b);
[tf,ri]=ismember(string(T.test_id),ids); [tb,bi]=ismember(string(T.bin_id),bins); if ~all(tf&tb)||height(T)~=n*b,error('Label alignment invalid %s.',sim);end
key=sub2ind([n,b],ri,bi); if numel(unique(key))~=n*b,error('Duplicate label key.');end
aa=str2double(string(T.applicable)); vv=str2double(string(T.available)); val=str2double(string(T.value)); st=string(T.state);
if any(~ismember(aa,[0,1]))||any(~ismember(vv,[0,1]))||any(aa==0&vv~=0)||any(aa==1&vv==1&~ismember(val,[0,1]))||any((aa==0|vv==0)&isfinite(val)),error('Invalid masks/states.');end
if any(aa==0&~ismember(st,["inapplicable","unsupported"]))||any(aa==1&vv==0&st~="unavailable")|| ...
        any(aa==1&vv==1&~ismember(st,["observed_zero","observed_hit"]))|| ...
        any(aa==1&vv==1&((st=="observed_zero")~=(val==0))),error('Unsupported/inapplicable/unavailable/observed states are inconsistent.');end
Y(key)=val;app(key)=aa==1;av(key)=vv==1;state(key)=st;
CT=C(string(C.simulator)==sim,:);[tc,ci]=ismember(ids,string(CT.test_id)); if ~all(tc),error('Cost rows misaligned.');end; CT=CT(ci,:);
cost=str2double(string(CT.observed_cycles)); if any(~isfinite(cost)|cost<=0)||any(string(CT.status)~="PASS")||any(string(CT.cycles_unit)~="cycle"),error('Invalid observed cost.');end
raw=[str2double(string(F.program_bytes)),str2double(string(F.unique_byte_values))]; cfg=string(F.configuration); lev=unique(cfg(split=="train"),'stable'); X=[raw, double(cfg==lev')];
reachable=string(D.reachability)=="reachable" & any(app&av,1)'; rare=false(b,1);
MD=readtable(fullfile(pwd,'reports','stage11_matlab_ml','metrics_per_bin.csv'),'TextType','string'); MD=MD(string(MD.simulator)==sim,:);[rOK,rLoc]=ismember(bins,string(MD.bin_id));if ~all(rOK),error('Stage 11 rare-bin dictionary does not align.');end;rare=str2double(string(MD.rare_positive(rLoc)))==1 & reachable;
feat=string(F.test_id); [~,fi]=ismember(ids,feat);
x=struct('sim',sim,'ids',ids,'split',split,'group',groups,'Y',Y,'valid',app&av&isfinite(Y), ...
 'applicable',app,'available',av,'state',state,'cycles',cost,'X',X(fi,:),'bins',bins, ...
 'reachable',reachable,'rare',rare);
end
function ix=mapIds(wanted,allids),[ok,ix]=ismember(wanted,allids);if ~all(ok),error('Unknown logical test ID.');end,end
function [m,fitLogRow,snap]=fitAcquiredModel(x,acquired,phase,~,roundNo)
if isempty(acquired)||any(x.split(acquired)~="train"),error('Fit labels must be acquired training rows only.');end
X=x.X(acquired,:); mu=mean(X,1); sd=std(X,0,1);sd(~isfinite(sd)|sd==0)=1;Z=(X-mu)./sd; Z=[ones(size(Z,1),1),Z];
n=numel(x.ids);B=numel(x.bins);P=NaN(n,B); beta=zeros(size(Z,2),B);constant=false(1,B);
for b=1:B,q=x.valid(acquired,b); y=x.Y(acquired(q),b); if isempty(y),P(:,b)=NaN;constant(b)=true;continue;end
 if all(y==y(1)),P(:,b)=min(max((sum(y)+1)/(numel(y)+2),.001),.999);constant(b)=true;continue;end
 zb=Z(q,:); yb=reshape(y,[],1); A=zb'*zb+diag([0;ones(size(Z,2)-1,1)]); rhs=zb'*yb-.5*sum(zb,1)'; beta(:,b)=A\rhs;
 z=[ones(n,1),((x.X-mu)./sd)];P(:,b)=1./(1+exp(-max(min(z*beta(:,b),30),-30)));
end
q=acquired(isfinite(x.cycles(acquired)));costBeta=[mean(x.cycles(q)),zeros(1,size(x.X,2))];
if numel(q)>=2,Zc=[ones(numel(q),1),((x.X(q,:)-mu)./sd)];costBeta=((Zc'*Zc+diag([0;ones(size(Zc,2)-1,1)]))\(Zc'*log(x.cycles(q(:)))) )';end
z=[ones(n,1),((x.X-mu)./sd)]; pc=max(exp(z*costBeta'),1e-6);
m=struct('probabilities',P,'predictedCycles',pc);fitLogRow=struct('simulator',x.sim,'phase',phase,'round',roundNo,'fit_ids',strjoin(x.ids(acquired),';'),'fit_count',numel(acquired),'preprocess_ids',strjoin(x.ids(acquired),';'),'constant_bins',sum(constant));
snap=struct('simulator',x.sim,'model_version',x.sim+"_"+phase+"_r"+roundNo,'phase',phase,'round',roundNo,'fit_ids',strjoin(x.ids(acquired),';'),'beta',beta,'cost_beta',costBeta,'mean',mu,'scale',sd,'constant_bins',constant);
end
function c=coverageFrom(x,idx), c=any(x.valid(idx,:)&x.Y(idx,:)==1,1)'; end
function [choice,grid]=tuneOnValidation(x,initial,P,cost,pool,startCov)
grid=struct([]); best=-Inf; choices=["uncertainty","marginal_coverage","cost_aware"];
for meth=choices
 for bs=[4,8], for cnt=[8,16,24]
  [ord,~,~,~]=rankCandidates(P,x.applicable(pool,:),cost,x.ids(pool),startCov,x.reachable,meth,.5,cnt,0,0);
  take=ord(1:min([bs*ceil(cnt/bs),cnt,numel(ord)])); cov=startCov; for j=take',cov=cov|any(x.valid(pool(j),:)&x.Y(pool(j),:)==1,1)';end
  gain=sum(cov&x.reachable)-sum(startCov&x.reachable); score=gain/max(1,numel(take));
  row=struct('simulator',x.sim,'method',meth,'batch_size',bs,'stop_count',cnt,'validation_selected',numel(take),'validation_new_reachable_bins',gain,'validation_gain_per_test',score);grid=appendStruct(grid,row);
  if score>best,best=score;choice=row;end
 end,end
end
choice.cost_exponent=.5; choice.predicted_cycle_budget=sum(cost)*min(choice.stop_count,numel(cost))/numel(cost)*.5;
end
function [order,score,gain,uncert]=rankCandidates(P,applicable,cost,ids,covered,reach,method,alpha,~,~,~)
mask=logical(applicable)&isfinite(P);uncert=1-abs(2*P-1);uncert(~mask)=0; P(~mask)=0; gain=sum(P.*mask.*(reach(:)'.*double(~covered(:)')),2);
switch string(method)
case "uncertainty", score=sum(uncert,2);
case "cost_aware", score=gain./max(cost,eps).^alpha;
otherwise,score=gain;
end
score(~isfinite(score))=-Inf; T=table(-score(:),string(ids(:)),'VariableNames',{'negative_score','stable_id'}); [~,order]=sortrows(T,{'negative_score','stable_id'});
end
function runActiveLearningExamples()
P=[.5 .5;.5 .5];app=true(2,2);ids=["z","a"];[ord,~,~,~]=rankCandidates(P,app,[1;1],ids,false(2,1),true(2,1),"marginal_coverage",0,2,0,0);
if ~isequal(ord(:),[2;1]),error('Stable-ID tie-breaking example failed.');end
[picked,rejected]=underPredictedBudget([1;2],[3;4],3,2);if ~isequal(picked,1)||~isequal(rejected,2),error('Predicted-budget boundary example failed.');end
app(1,:)=false(1,2);[~,~,g,~]=rankCandidates(P,app,[1;1],ids,false(2,1),true(2,1),"marginal_coverage",0,2,0,0);if g(1)~=0,error('Applicability-mask example failed.');end
end
function [picked,rejected]=underPredictedBudget(order,cost,budget,count)
picked=[];rejected=[];spent=0;for i=order(:)',if numel(picked)>=count,break;end;if spent+cost(i)<=budget,picked(end+1)=i;spent=spent+cost(i);else,rejected(end+1)=i;end,end
end
function state=runPoolReplay(x,key,method,seed,initial,stopCount,batch,alpha,budget,pauseAfter,checkpoint)
if isempty(checkpoint),state=struct('run_key',key,'acquired',initial(:)','round',0,'acquisitionRows',struct([]),'scoreRows',struct([]),'predictionRows',struct([]),'observationRows',struct([]),'curveRows',struct([]),'fitRows',struct([]),'modelVersions',struct([]));c0=coverageFrom(x,initial);state.curveRows=appendStruct(state.curveRows,curveRecord("training_replay",x.sim,method,seed,0,sum(c0&x.reachable),sum(x.reachable),sum(c0&x.rare),sum(x.rare&x.reachable),0,0,0,budget));else,state=checkpoint;end
pool=find(x.split=="train");
while numel(state.acquired)<min(stopCount+numel(initial),numel(pool))
 state.round=state.round+1;[m,fl,sn]=fitAcquiredModel(x,state.acquired,"training_replay",0,state.round);fl.run_key=key;state.fitRows=appendStruct(state.fitRows,fl);state.modelVersions=appendStruct(state.modelVersions,sn);
 cand=setdiff(pool,state.acquired,'stable'); if isempty(cand),break;end
 cover=coverageFrom(x,state.acquired);[ord,scores,gains,unc]=rankCandidates(m.probabilities(cand,:),x.applicable(cand,:),m.predictedCycles(cand),x.ids(cand),cover,x.reachable,method,alpha,stopCount,0,0);
 if method=="random",rng(seed+state.round,'twister');ord=randperm(numel(cand))';scores=rand(numel(cand),1);end
 remain=stopCount-(numel(state.acquired)-numel(initial)); lim=min([batch,remain,numel(ord)]); spent=0;if ~isempty(state.acquisitionRows),spent=sum([state.acquisitionRows.predicted_cycles]);end; [take,rej]=underPredictedBudget(ord,m.predictedCycles(cand),budget-spent,lim); if isempty(take),break;end
 for j=1:numel(cand),state.scoreRows=appendStruct(state.scoreRows,struct('run_key',key,'round',state.round,'simulator',x.sim,'test_id',x.ids(cand(j)),'score',scores(j),'marginal_gain',gains(j),'uncertainty',sum(unc(j,:)),'predicted_cycles',m.predictedCycles(cand(j)),'candidate_pool',true));end
 for r=1:numel(take),ix=cand(take(r));state.acquired(end+1)=ix;state.acquisitionRows=appendStruct(state.acquisitionRows,struct('run_key',key,'round',state.round,'rank_in_round',r,'simulator',x.sim,'test_id',x.ids(ix),'seed',seed,'policy',method,'predicted_cycles',m.predictedCycles(ix),'observed_cycles',x.cycles(ix),'model_version',sn.model_version,'budget_rejected_candidates',numel(rej)));for b=1:numel(x.bins),state.predictionRows=appendStruct(state.predictionRows,struct('run_key',key,'round',state.round,'test_id',x.ids(ix),'simulator',x.sim,'bin_id',x.bins(b),'probability',m.probabilities(ix,b),'applicable',x.applicable(ix,b),'evidence_available',x.available(ix,b)));state.observationRows=appendStruct(state.observationRows,struct('run_key',key,'round',state.round,'test_id',x.ids(ix),'simulator',x.sim,'bin_id',x.bins(b),'state',x.state(ix,b),'value',x.Y(ix,b),'evaluation_only',true));end,end
 c=coverageFrom(x,state.acquired);state.curveRows=appendStruct(state.curveRows,curveRecord("training_replay",x.sim,method,seed,numel(state.acquired)-numel(initial),sum(c&x.reachable),sum(x.reachable),sum(c&x.rare),sum(x.rare&x.reachable),0,sum([state.acquisitionRows.predicted_cycles]),sum([state.acquisitionRows.observed_cycles]),budget));
 if state.round>=pauseAfter,break;end
end
end
function row=curveRecord(scope,sim,method,seed,acquired,covered,den,rareCovered,rareDen,newRare,pred,observed,budget)
row=struct('scope',scope,'simulator',sim,'policy',method,'seed',seed,'acquired_count',acquired,'covered_reachable_bins',covered,'reachable_denominator',den,'rare_bins_covered',rareCovered,'rare_bin_denominator',rareDen,'new_rare_bins_this_round',newRare,'predicted_cycles_spent',pred,'observed_cycles_spent',observed,'predicted_cycle_budget',budget,'observed_budget_overrun',max(0,observed-budget));
end
function s=summarizeState(state,x,method,seed,choice)
c=coverageFrom(x,state.acquired);c0=coverageFrom(x,state.acquired(1:min(16,numel(state.acquired)))); acq=state.acquired(min(17,numel(state.acquired)+1):end);obs=0;if ~isempty(acq),obs=sum(x.cycles(acq));end; s=struct('run_key',state.run_key,'simulator',x.sim,'policy',method,'seed',seed,'initial_count',16,'initial_covered_bins',sum(c0&x.reachable),'new_bins_after_acquisition',sum(c&~c0&x.reachable),'acquired_count',numel(state.acquired)-16,'total_labeled_count',numel(state.acquired),'covered_reachable_bins',sum(c&x.reachable),'reachable_denominator',sum(x.reachable),'rare_bins_covered',sum(c&x.rare),'observed_cycles',obs,'predicted_budget',choice.predicted_cycle_budget,'observed_budget_overrun',max(0,obs-choice.predicted_cycle_budget),'small_corpus_exploratory',true);
end
function r=randomVariability(s)
r=struct([]);for sim=unique(string({s.simulator})),q=s(string({s.simulator})==sim & string({s.policy})=="random"); if isempty(q),continue;end;r=appendStruct(r,struct('simulator',sim,'seed_count',numel(q),'mean_covered_bins',mean([q.covered_reachable_bins]),'std_covered_bins',std([q.covered_reachable_bins]),'mean_observed_cycles',mean([q.observed_cycles]),'std_observed_cycles',std([q.observed_cycles])));end
end
function v=meanOrNaN(x),if isempty(x),v=NaN;else,v=mean(x);end,end
function k=makeRunKey(sim,method,seed),k=sim+"_"+method+"_"+seed;end
function c=runtimeConfiguration(choices,initialIDs,seed,randomSeeds,resume)
products=ver;ti=find(contains(string({products.Name}),"Statistics and Machine Learning Toolbox"),1);if isempty(ti),error('Required toolbox not installed.');end
c=struct('schema_version','stage13-active-learning-1.0.0','runtime_release',version('-release'),'runtime_version',version,'statistics_toolbox_license',license('test','Statistics_Toolbox'),'statistics_toolbox_name',products(ti).Name,'statistics_toolbox_version',products(ti).Version,'split',struct('train',196,'validation',46,'test',40),'initial_seed',seed,'initial_count',numel(initialIDs),'initial_ids',initialIDs,'random_seeds',randomSeeds,'policy_choices',choices,'offline_replay_only',true,'test_labels_used_for_updates',false,'resume_equivalence',resume.passed,'limitations','Exploratory small corpus; no promised coverage gains, cost savings, superiority, or generalization.');
end
function writeStructTable(p,s),if isempty(s),writetable(table(),p);else,writetable(struct2table(s),p);end,end
function writeJson(p,x),fid=fopen(p,'w');cc=onCleanup(@()fclose(fid));fwrite(fid,jsonencode(x,'PrettyPrint',true),'char');fwrite(fid,newline,'char');end
function writeText(p,x),fid=fopen(p,'w');cc=onCleanup(@()fclose(fid));fwrite(fid,x,'char');end
function m=makeManifest(outDir,hashes)
files=dir(fullfile(outDir,'*'));outputs=struct('path',{},'sha256',{});for k=1:numel(files),if files(k).isdir||ismember(files(k).name,{'manifest.json','resume_checkpoint.mat'}),continue;end;outputs(end+1)=struct('path',files(k).name,'sha256',shaPortable(fullfile(outDir,files(k).name)));end
m=struct('schema_version','stage13-active-learning-1.0.0','base_commit','db3835f093c4ef955757aa2ac3b67488189000af','inputs',hashes,'outputs',outputs,'scope','offline saved-observation replay; simulators were not run');
end
function validateStage13(root,outDir)
req={'configuration.json','manifest.json','validation_evidence.txt','active_replay.mat','active_acquisitions.csv','fit_provenance.csv','final_test_predictions.csv','final_test_observations.csv','learning_curves.csv'};for k=1:numel(req),if ~isfile(fullfile(outDir,req{k})),error('Missing Stage 13 output %s.',req{k});end,end
m=jsondecode(fileread(fullfile(outDir,'manifest.json')));for k=1:numel(m.inputs),p=fullfile(root,strrep(char(m.inputs(k).path),'/',filesep));if endsWith(string(m.inputs(k).path),"metrics_per_bin.csv"),ih=shaRawFile(p);else,ih=shaPortable(p);end;if ~isfile(p)||~strcmpi(ih,m.inputs(k).sha256),error('Stage 13 input hash mismatch: %s',m.inputs(k).path);end,end
for k=1:numel(m.outputs),p=fullfile(outDir,m.outputs(k).path);if ~isfile(p)||~strcmpi(shaPortable(p),m.outputs(k).sha256),error('Stage 13 output hash mismatch: %s',m.outputs(k).path);end,end
a=readtable(fullfile(outDir,'active_acquisitions.csv'),'TextType','string');f=readtable(fullfile(outDir,'fit_provenance.csv'),'TextType','string');t=readtable(fullfile(outDir,'final_test_predictions.csv'),'TextType','string');
if numel(unique(string(a.run_key)+"|"+string(a.test_id)))~=height(a),error('Repeated acquisition.');end
if any(str2double(string(t.actual_label_included))~=0),error('Test prediction leakage marker invalid.');end
splitTable=readtable(fullfile(root,'reports','stage10_dataset','split_assignments.csv'),'TextType','string');trainIDs=string(splitTable.test_id(string(splitTable.split)=="train"));
if sum(string(splitTable.split)=="train")~=196||sum(string(splitTable.split)=="validation")~=46||sum(string(splitTable.split)=="test")~=40,error('Frozen 196/46/40 split changed.');end
for g=unique(string(splitTable.group_id))'
    groupSplits=unique(string(splitTable.split(string(splitTable.group_id)==g)));
    if numel(groupSplits)~=1,error('Frozen split group overlap detected.');end
end
init=readtable(fullfile(outDir,'initial_labeled_ids.csv'),'TextType','string');
for k=1:height(a),if ~ismember(string(a.test_id(k)),trainIDs),error('An acquisition came from outside training split.');end,end
for k=1:height(f)
 fitIDs=string(strsplit(char(f.fit_ids(k)),';'));if any(~ismember(fitIDs,trainIDs)),error('Model/preprocessing fit used labels outside frozen training IDs.');end
 expected=string(init.test_id(string(init.simulator)==string(f.simulator(k)))); runRows=a(string(a.run_key)==string(f.run_key(k)),:);
 if string(f.phase(k))=="training_replay",runRows=runRows(str2double(string(runRows.round))<str2double(string(f.round(k))),:);end
 if string(f.phase(k))~="validation_tune",expected=[expected;string(runRows.test_id)];end
 if ~isequal(sort(unique(fitIDs(:))),sort(unique(expected(:)))),error('Fit consumed labels outside its acquired round state: %s round %s.',f.run_key(k),f.round(k));end
end
if ~contains(fileread(fullfile(outDir,'validation_evidence.txt')),'checkpoint_resume_equivalence=PASS'),error('Resume validation evidence missing.');end
% Stable-ID row and key checks; NaN probabilities remain explicit as unavailable.
if height(t)~=40*316*2||numel(unique(string(t.simulator)+"|"+string(t.test_id)+"|"+string(t.bin_id)))~=height(t),error('Heldout prediction row alignment or stable keys invalid.');end
if any(str2double(string(t.prediction_available))==0 & isfinite(str2double(string(t.predicted_hit_probability)))),error('Unavailable prediction was serialized as a numeric target.');end
R=load(fullfile(outDir,'active_replay.mat'),'selectedStates','resumeEvidence','modelVersions');if numel(R.selectedStates)~=2||~R.resumeEvidence.passed||isempty(R.modelVersions),error('Replay serialization round-trip failed.');end
disp('Stage 13 standalone validation PASS');
end
function h=shaText(p),s=fileread(p);s=strrep(s,sprintf('\r\n'),sprintf('\n'));s=strrep(s,sprintf('\r'),sprintf('\n'));h=shaBytes(uint8(unicode2native(s,'UTF-8')));end
function h=shaPortable(p),[~,~,e]=fileparts(p);if any(strcmpi(e,{'.csv','.json','.txt','.m','.bat','.md'})),h=shaText(p);else,f=fopen(p,'r');c=onCleanup(@()fclose(f));h=shaBytes(fread(f,Inf,'*uint8'));end,end
function h=shaRawFile(p),f=fopen(p,'r');c=onCleanup(@()fclose(f));h=shaBytes(fread(f,Inf,'*uint8'));end

function runStage13(root,outDir)
runActiveLearningExamples();
if ~license('test','Statistics_Toolbox')
    error('Statistics and Machine Learning Toolbox license is required to validate the installed dependency.');
end
if ~isfolder(outDir), mkdir(outDir); end
[F,S,L,D,C,bins,hashes]=loadStageData(root);
for rel=["scripts/machine_learning/stage13_run.m","scripts/machine_learning/run_stage13_matlab.bat","scripts/machine_learning/validate_stage13_matlab.bat"]
    hashes(end+1)=struct('path',rel,'sha256',shaPortable(fullfile(root,strrep(rel,'/',filesep)))); %#ok<AGROW>
end
ids=string(F.test_id); [ok,loc]=ismember(ids,string(S.test_id));
if ~all(ok) || numel(unique(ids))~=282 || numel(unique(string(S.test_id)))~=282
    error('Frozen logical-test IDs are duplicated or misaligned.');
end
split=string(S.split(loc)); groups=string(S.group_id(loc));
if sum(split=="train")~=196 || sum(split=="validation")~=46 || sum(split=="test")~=40
    error('Frozen grouped split must remain 196/46/40.');
end
for g=unique(groups)'
    if numel(unique(split(groups==g)))~=1, error('Related logical tests cross the frozen split: %s.',g); end
end
seedInitial=13013; rng(seedInitial,'twister'); trainIdx=find(split=="train"); initIdx=sort(trainIdx(randperm(numel(trainIdx),16)));
initialIDs=ids(initIdx); simulators=["xsim","verilator"]; data=struct([]);
for si=1:numel(simulators), data=appendStruct(data,buildSimulator(simulators(si),F,ids,split,groups,L,D,C,bins)); end

validationGrid=struct([]); policyChoices=struct([]); initialRows=struct([]); validationFits=struct([]);
for si=1:numel(data)
    x=data(si); initial=mapIds(initialIDs,x.ids); valPool=find(x.split=="validation");
    [initialModel,initLog,initSnapshot]=fitAcquiredModel(x,initial,"validation_tune",0,0);
    initLog.run_key="validation_tune_"+x.sim; validationFits=appendStruct(validationFits,initLog);
    Pval=initialModel.probabilities(valPool,:); Cval=initialModel.predictedCycles(valPool);
    startCovered=coverageFrom(x,initial);
    [choice,gridPart]=tuneOnValidation(x,initial,Pval,Cval,valPool,startCovered);
    validationGrid=[validationGrid,gridPart];
    policyChoices=appendStruct(policyChoices,choice);
    for k=1:numel(initial)
        initialRows=appendStruct(initialRows,struct('simulator',x.sim,'seed',seedInitial, ...
            'initial_rank',k,'test_id',x.ids(initial(k)),'split',"train",'group_id',x.group(initial(k)), ...
            'observed_cycles_used_for_initial_fit',x.cycles(initial(k))));
    end
    % Initial models are validation-only; fit IDs are always the same acquired training subset.
    %#ok<NASGU> initLog initSnapshot
end

acquisitions=struct([]); scoreRows=struct([]); predRows=struct([]); obsRows=struct([]);
curveRows=struct([]); fitRows=validationFits; summaries=struct([]); modelVersions=struct([]);
randomSeeds=2301:2310; selectedStates=struct([]); resumeEvidence=struct('passed',false,'run_key',"",'checkpoint_round',1);
for si=1:numel(data)
    x=data(si); initial=mapIds(initialIDs,x.ids); choice=policyChoices(si);
    methodList=["uncertainty","marginal_coverage","cost_aware"];
    for mi=1:numel(methodList)
        method=methodList(mi); seed=0; alpha=choice.cost_exponent; runKey=makeRunKey(x.sim,method,seed);
        state=runPoolReplay(x,runKey,method,seed,initial,choice.stop_count,choice.batch_size,alpha,choice.predicted_cycle_budget,Inf,[]);
        acquisitions=[acquisitions,state.acquisitionRows]; scoreRows=[scoreRows,state.scoreRows]; %#ok<AGROW>
        predRows=[predRows,state.predictionRows]; obsRows=[obsRows,state.observationRows]; %#ok<AGROW>
        curveRows=[curveRows,state.curveRows]; fitRows=[fitRows,state.fitRows]; %#ok<AGROW>
        modelVersions=[modelVersions,state.modelVersions]; %#ok<AGROW>
        summaries=appendStruct(summaries,summarizeState(state,x,method,seed,choice));
        if method==choice.method && seed==0, selectedStates=appendStruct(selectedStates,state); end
        if method=="marginal_coverage" && si==1
            partial=runPoolReplay(x,runKey,method,seed,initial,choice.stop_count,choice.batch_size,alpha,choice.predicted_cycle_budget,1,[]);
            cpPath=fullfile(outDir,'resume_checkpoint.mat'); save(cpPath,'partial','-v7.3');
            loaded=load(cpPath,'partial'); delete(cpPath); resumed=runPoolReplay(x,runKey,method,seed,initial,choice.stop_count, ...
                choice.batch_size,alpha,choice.predicted_cycle_budget,Inf,loaded.partial);
            if ~isequal(string({state.acquisitionRows.test_id}),string({resumed.acquisitionRows.test_id})) || ...
                    ~isequal(string({state.acquisitionRows.model_version}),string({resumed.acquisitionRows.model_version}))
                error('Checkpoint/resume diverged from uninterrupted replay.');
            end
            resumeEvidence=struct('passed',true,'run_key',runKey,'checkpoint_round',1);
        end
    end
    for seed=randomSeeds
        method="random"; alpha=choice.cost_exponent; runKey=makeRunKey(x.sim,method,seed);
        state=runPoolReplay(x,runKey,method,seed,initial,choice.stop_count,choice.batch_size,alpha,choice.predicted_cycle_budget,Inf,[]);
        acquisitions=[acquisitions,state.acquisitionRows]; scoreRows=[scoreRows,state.scoreRows]; %#ok<AGROW>
        predRows=[predRows,state.predictionRows]; obsRows=[obsRows,state.observationRows]; %#ok<AGROW>
        curveRows=[curveRows,state.curveRows]; fitRows=[fitRows,state.fitRows]; %#ok<AGROW>
        modelVersions=[modelVersions,state.modelVersions]; %#ok<AGROW>
        summaries=appendStruct(summaries,summarizeState(state,x,method,seed,choice));
    end
end

testPredictions=struct([]); testObservations=struct([]); testMetrics=struct([]); testCurves=struct([]); testSummaries=struct([]);
for si=1:numel(data)
    x=data(si); choice=policyChoices(si); runKey=makeRunKey(x.sim,choice.method,0);
    st=find(string({selectedStates.run_key})==runKey,1);
    if isempty(st), error('Validation-selected training replay missing for %s.',x.sim); end
    finalState=selectedStates(st); acquired=finalState.acquired;
    [mdl,fitLog,snapshot]=fitAcquiredModel(x,acquired,"final_test_model",0,finalState.round+1);fitLog.run_key=runKey;
    fitRows=appendStruct(fitRows,fitLog); modelVersions=appendStruct(modelVersions,snapshot);
    testPool=find(x.split=="test"); testCover=coverageFrom(x,acquired);
    [order,score,gain,uncertainty]=rankCandidates(mdl.probabilities(testPool,:),x.applicable(testPool,:), ...
        mdl.predictedCycles(testPool),x.ids(testPool),testCover,x.reachable,choice.method, ...
        choice.cost_exponent,choice.stop_count,0,0);
    [picked,rejected]=underPredictedBudget(order,mdl.predictedCycles(testPool),choice.predicted_cycle_budget,choice.stop_count);
    predSpent=sum(mdl.predictedCycles(testPool(picked))); actualSpent=0; covered=testCover;
    testCurves=appendStruct(testCurves,curveRecord("heldout_test",x.sim,choice.method,0,0, ...
        sum(testCover & x.reachable),sum(x.reachable),sum(testCover & x.rare),sum(x.rare & x.reachable), ...
        0,0,0,choice.predicted_cycle_budget));
    for r=1:numel(testPool)
        i=testPool(r); rank=find(order==r,1); selected=ismember(r,picked);
        for b=1:numel(x.bins)
            predAvailable=logical(x.applicable(i,b))&&isfinite(mdl.probabilities(i,b)); predProbability=NaN;
            if predAvailable,predProbability=mdl.probabilities(i,b);end
            testPredictions=appendStruct(testPredictions,struct('simulator',x.sim,'test_id',x.ids(i), ...
                'split',"test",'bin_id',x.bins(b),'model_version',snapshot.model_version, ...
                'applicable',x.applicable(i,b),'evidence_available',x.available(i,b), ...
                'prediction_available',predAvailable, ...
                'predicted_hit_probability',predProbability,'acquisition_rank',rank, ...
                'selected_under_validation_policy',selected,'actual_label_included',false));
        end
    end
    % The complete test ranking is now frozen. Reveal observations only for offline scoring below.
    for k=1:numel(picked)
        i=testPool(picked(k)); hit=x.valid(i,:)' & x.reachable(:) & x.Y(i,:)'==1;
        new=hit & ~covered; covered=covered | hit; actualSpent=actualSpent+x.cycles(i);
        for b=1:numel(x.bins)
            testObservations=appendStruct(testObservations,struct('simulator',x.sim,'test_id',x.ids(i), ...
                'split',"test",'bin_id',x.bins(b),'state',x.state(i,b),'value',x.Y(i,b), ...
                'applicable',x.applicable(i,b),'evidence_available',x.available(i,b),'evaluation_only',true));
        end
        testCurves=appendStruct(testCurves,curveRecord("heldout_test",x.sim,choice.method,0,k, ...
            sum(covered & x.reachable),sum(x.reachable),sum(covered & x.rare),sum(x.rare & x.reachable), ...
            sum(new & x.rare),predSpent,actualSpent,choice.predicted_cycle_budget));
    end
    obs=x.valid(testPool,:) & x.reachable(:)'; p=mdl.probabilities(testPool,:);
    for b=1:numel(x.bins)
        q=obs(:,b) & isfinite(p(:,b)); yy=x.Y(testPool(q),b); pp=p(q,b);
        testMetrics=appendStruct(testMetrics,struct('simulator',x.sim,'bin_id',x.bins(b), ...
            'test_support',numel(yy),'positive_support',sum(yy==1),'negative_support',sum(yy==0), ...
            'brier',meanOrNaN((pp-yy).^2),'rare_bin',x.rare(b),'reachable',x.reachable(b), ...
            'metric_scope',"one_shot_final_test_after_policy_lock"));
    end
    aggregateMask=obs & isfinite(p); yy=x.Y(testPool,:); den=sum(aggregateMask,'all');
    actualHit=any(yy==1 & obs,1)';
    testSummaries=appendStruct(testSummaries,struct('simulator',x.sim,'policy',choice.method, ...
        'test_logical_candidates',numel(testPool),'selected_test_count',numel(picked), ...
        'budget_rejections',numel(rejected),'predicted_cycle_budget',choice.predicted_cycle_budget, ...
        'predicted_cycles_spent',predSpent,'observed_cycles_spent_evaluation_only',actualSpent, ...
        'observed_budget_overrun_cycles_evaluation_only',max(0,actualSpent-choice.predicted_cycle_budget), ...
        'prediction_budget_overrun_evaluation_only',actualSpent>choice.predicted_cycle_budget, ...
        'initial_training_covered_bins',sum(testCover & x.reachable), ...
        'test_covered_bins_after_selected_prefix',sum(covered & x.reachable), ...
        'reachable_denominator',sum(x.reachable),'new_test_bins',sum(covered & x.reachable)-sum(testCover & x.reachable), ...
        'test_micro_brier',meanOrNaN((p(aggregateMask)-yy(aggregateMask)).^2), ...
        'prediction_support',den,'actual_test_bins_with_any_hit',sum(actualHit & x.reachable), ...
        'test_outcomes_used_for_updates',false));
end

config=runtimeConfiguration(policyChoices,initialIDs,seedInitial,randomSeeds,resumeEvidence);
writeStructTable(fullfile(outDir,'initial_labeled_ids.csv'),initialRows);
writeStructTable(fullfile(outDir,'validation_policy_grid.csv'),validationGrid);
writeStructTable(fullfile(outDir,'policy_choices.csv'),policyChoices);
writeStructTable(fullfile(outDir,'active_acquisitions.csv'),acquisitions);
writeStructTable(fullfile(outDir,'round_candidate_scores.csv'),scoreRows);
writeStructTable(fullfile(outDir,'acquired_predictions.csv'),predRows);
writeStructTable(fullfile(outDir,'acquired_observations.csv'),obsRows);
writeStructTable(fullfile(outDir,'learning_curves.csv'),curveRows);
writeStructTable(fullfile(outDir,'fit_provenance.csv'),fitRows);
writeStructTable(fullfile(outDir,'final_test_predictions.csv'),testPredictions);
writeStructTable(fullfile(outDir,'final_test_observations.csv'),testObservations);
writeStructTable(fullfile(outDir,'final_test_metrics_per_bin.csv'),testMetrics);
writeStructTable(fullfile(outDir,'final_test_curves.csv'),testCurves);
writeStructTable(fullfile(outDir,'final_test_summary.csv'),testSummaries);
writeStructTable(fullfile(outDir,'random_seed_variability.csv'),randomVariability(summaries));
writeStructTable(fullfile(outDir,'run_summary.csv'),summaries);
writeJson(fullfile(outDir,'configuration.json'),config);
save(fullfile(outDir,'active_replay.mat'),'modelVersions','resumeEvidence','selectedStates','policyChoices','-v7.3');
writeText(fullfile(outDir,'validation_evidence.txt'),sprintf(['STAGE13 MATLAB VALIDATION PASS\nrelease=%s\n' ...
    'logical_tests=282\ntrain_validation_test=196,46,40\nsimulator_separation=true\n' ...
    'fit_scope=currently_acquired_training_labels_and_cycles_only\nheldout_test_updates=false\n' ...
    'offline_replay_only=true\ncheckpoint_resume_equivalence=PASS\n'],version('-release')));
manifest=makeManifest(outDir,hashes); writeJson(fullfile(outDir,'manifest.json'),manifest);
validateStage13(root,outDir);
end

function h=shaBytes(bytes),md=java.security.MessageDigest.getInstance('SHA-256');md.update(typecast(bytes(:),'int8'));d=typecast(md.digest(),'uint8');h=lower(string(reshape(dec2hex(d,2).',1,[])));end
function rows=appendStruct(rows,row),if isempty(rows),rows=row;else,rows(end+1)=row;end,end
