/* Deterministic teaching simulator. Ticks are illustrative, never benchmarks. */
(function (host) {
  const definitions = [
    {id:'menu',code:'C01.1',name:'查菜单',deps:[],service:'tool',duration:2,why:'门店已确定，可直接查询菜单。'},
    {id:'offer',code:'C01.2',name:'查优惠',deps:[],service:'tool',duration:4,why:'本例优惠查询不依赖菜单，可与菜单并行。'},
    {id:'compare',code:'C01.3',name:'比较方案',deps:['menu','offer'],service:'model',duration:3,why:'汇合点：必须拿到菜单和优惠两份结果。'},
    {id:'authorize',code:'C01.4',name:'确认授权',deps:['compare'],service:'human',duration:0,why:'等待用户同意方案；等待期间不占执行名额。'},
    {id:'order',code:'C01.5',name:'提交订单',deps:['authorize'],service:'tool',duration:2,why:'只有授权已完成，才能发起购买操作。'},
    {id:'verify',code:'C01.6',name:'核验订单',deps:['order'],service:'tool',duration:2,why:'读取订单状态，核对商品、金额及订单标识。'},
    {id:'receipt',code:'C01.7',name:'返回回执',deps:['verify'],service:'local',duration:1,why:'核验通过后，把回执交回原任务 C01。'}
  ];
  class Simulation {
    constructor(slots=2,slow=false){this.slots=slots;this.slow=slow;this.reset();}
    reset(){this.time=0;this.phase='incoming';this.nodes=definitions.map(d=>({...d,deps:[...d.deps],state:'unplanned',elapsed:0,duration:d.duration+(d.id==='offer'&&this.slow?4:0)}));this.events=[];this.record('收到委托 C01：帮我点一杯咖啡。');}
    record(text){this.events.push({time:this.time,text});}
    get done(){return this.phase==='done';}
    get authorizationRequired(){return this.nodes.find(n=>n.id==='authorize').state==='waiting';}
    get running(){return this.nodes.filter(n=>n.state==='running');}
    refresh(){for(const n of this.nodes){if(n.state!=='blocked')continue;if(n.deps.every(id=>this.nodes.find(p=>p.id===id).state==='success')){n.state=n.service==='human'?'waiting':'ready';n.readyAt=this.time;this.record(n.code+' '+n.name+(n.state==='waiting'?'：等待用户确认，不占执行名额。':'：依赖已满足，进入就绪集合。'));}}}
    tick(){
      if(this.done||this.authorizationRequired)return false;
      this.time++;
      if(this.phase==='incoming'){this.phase='assigned';this.record('S1：委托交给能力与权限匹配的 Agent A（本例固定选择）。');return true;}
      if(this.phase==='assigned'){this.phase='planned';this.nodes.forEach(n=>n.state='blocked');this.record('Agent 将 C01 拆成七个步骤，建立依赖图；规划给出调度输入。');this.refresh();return true;}
      this.phase='running';
      for(const n of this.running){n.elapsed++;if(n.elapsed>=n.duration){n.state='success';this.record(n.code+' '+n.name+'完成，结果写回 C01。');}}
      this.refresh();
      let free=this.slots-this.running.length;
      for(const n of [...this.nodes].sort((a,b)=>(a.readyAt??Infinity)-(b.readyAt??Infinity))){if(n.state==='ready'&&free>0){n.state='running';n.started=this.time;free--;this.record('S2：启动 '+n.code+' '+n.name+'，占用一个执行名额。');}}
      if(this.nodes.every(n=>n.state==='success')){this.phase='done';this.record('C01 完成：订单回执已核验；不代表咖啡已经送达。');}
      return true;
    }
    authorize(){if(!this.authorizationRequired)return false;const n=this.nodes.find(n=>n.id==='authorize');n.state='success';this.record('演示用户确认方案；下单获授权。');this.refresh();return true;}
  }
  const api={Simulation,definitions};if(typeof module!=='undefined'&&module.exports)module.exports=api;else host.CoffeeSimulation=api;
})(globalThis);
