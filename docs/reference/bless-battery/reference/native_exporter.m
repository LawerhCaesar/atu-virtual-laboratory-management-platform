function export_platform_model
w=fileparts(mfilename('fullpath'));m='Powertrain_Comparison';
load_system('F:/Scripts for codex/Bless/Powertrain_Comparison.slx');
set_param(m,'SimulationCommand','update');
bs=sort(find_system(m,'LookUnderMasks','all','Type','block'));bs(strcmp(bs,m))=[];
blocks=struct([]);wiring=struct([]);n=0;
for k=1:numel(bs)
 b=bs{k};blocks(k).path=b;blocks(k).sid=get_param(b,'SID');blocks(k).type=get_param(b,'BlockType');
 blocks(k).parent=get_param(b,'Parent');blocks(k).position=get_param(b,'Position');
 params=get_param(b,'DialogParameters');values=struct;
 if ~isempty(params)
  names=sort(fieldnames(params));
  for j=1:numel(names),values.(names{j})=get_param(b,names{j});end
 end
 blocks(k).parameters=values;
 blocks(k).mask=struct('names',{get_param(b,'MaskNames')},'values',{get_param(b,'MaskValues')}, ...
  'variables',get_param(b,'MaskVariables'),'initialization',get_param(b,'MaskInitialization'));
 ph=get_param(b,'PortHandles');blocks(k).inputCount=numel(ph.Inport);blocks(k).outputCount=numel(ph.Outport);
 for j=1:numel(ph.Inport)
  l=get_param(ph.Inport(j),'Line');assert(l>0,'Disconnected input');sp=get_param(l,'SrcPortHandle');n=n+1;
  wiring(n).source=get_param(sp,'Parent');wiring(n).sourcePort=get_param(sp,'PortNumber');
  wiring(n).destination=b;wiring(n).destinationPort=j;
  wiring(n).signalName=get_param(get_param(sp,'Line'),'Name');
 end
end
sys=[{m};find_system(m,'LookUnderMasks','all','BlockType','SubSystem')];systems=struct([]);
for k=1:numel(sys)
 a=find_system(sys{k},'FindAll','on','SearchDepth',1,'Type','annotation');notes=cell(numel(a),1);
 for j=1:numel(a),notes{j}=get_param(a(j),'Text');end
 systems(k).path=sys{k};systems(k).notes=notes;
end
config=struct;names={'Solver','SolverType','FixedStep','StartTime','StopTime','RelTol','AbsTol','PostLoadFcn','InitFcn','StartFcn','StopFcn','SignalLogging','SignalLoggingName'};
for k=1:numel(names),config.(names{k})=get_param(m,names{k});end
workspace=get_param(m,'ModelWorkspace');vars=whos(workspace);entries=struct([]);
for k=1:numel(vars),entries(k).name=vars(k).name;entries(k).value=getVariable(workspace,vars(k).name);end
model=struct('model',m,'matlabVersion',version,'configuration',config,'blocks',blocks,'connections',wiring,'systems',systems,'workspace',entries);
fid=fopen(fullfile(w,'native_model.json'),'w');fwrite(fid,jsonencode(model,PrettyPrint=true));fclose(fid);
mkdir(fullfile(w,'golden'));
names={'default_cycle','battery_only','fuel_cell_start','hydrogen_empty','constant_speed','uphill_shortfall','regeneration_high_soc','hydrogen_depletion','priced_cycle','stationary'};
streams=struct([]);
for k=1:numel(names)
 z=load(fullfile(w,'..','..','bless_repair','work',['result_' names{k} '.mat']));
 for label={'comparison','electric','diesel','road'}
  name=label{1};t=z.out.logsout.get(name).Values;
  writematrix([t.Time t.Data],fullfile(w,'golden',[names{k} '__' name '.csv']));
  if k==1,streams(end+1).name=name;streams(end).columns=size(t.Data,2);end %#ok<AGROW>
 end
end
fid=fopen(fullfile(w,'streams.json'),'w');fwrite(fid,jsonencode(streams));fclose(fid);
fprintf('EXPORT_COMPLETE: %d blocks, %d connections, %d systems, 40 reference traces\n',numel(blocks),numel(wiring),numel(systems));
close_system(m,0);
end
