(() => {
const area=document.getElementById("playArea"), start=document.getElementById("start"), instructions=document.getElementById("instructions"), result=document.getElementById("result");
const points=[[0,0],[0,2],[1,3],[2,2],[3,3],[4,2],[4,4],[2,4]];
let running=false,started=0,tick=null,score=0,errors=0,attempts=0,correct=0,nextPoint=0;
function stats(){document.getElementById("score").textContent=score;document.getElementById("errors").textContent=errors;}
function render(){area.innerHTML="<h4>Click checkpoints in order: 1 → 8</h4><div id='grid'></div>";const grid=area.querySelector("#grid");
 for(let r=0;r<5;r++){const row=document.createElement("div");for(let c=0;c<5;c++){const i=points.findIndex(p=>p[0]===r&&p[1]===c);let label=i>=0?(i<nextPoint?"✓":String(i+1)):"·";const b=document.createElement("button");b.className="ms-btn";b.textContent=label;b.onclick=()=>{if(!running)return;attempts++;if(i===nextPoint){correct++;score+=10;nextPoint++;stats();if(nextPoint===points.length)finish();else render();}else{errors++;stats();}};row.appendChild(b);}grid.appendChild(row);}
}
function finish(){if(!running)return;running=false;clearInterval(tick);start.disabled=false;const elapsed=(Date.now()-started)/1000,accuracy=attempts?100*correct/attempts:0;
 result.hidden=false;result.textContent=`Finished! Score ${score}, checkpoint accuracy ${accuracy.toFixed(1)}%, errors ${errors}, time ${elapsed.toFixed(1)} seconds. Saving...`;
 fetch("/save_game_result",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({game_name:"Path Tracer",score,accuracy,reaction_time:0,completion_time:elapsed,errors,objects_caught:0,objects_missed:0,path_deviation:errors})}).then(r=>r.json()).then(d=>{result.textContent+=d.success?" Saved successfully.":" Could not save.";}).catch(()=>result.textContent+=" Server connection failed.");
}
start.onclick=()=>{running=true;started=Date.now();score=errors=attempts=correct=nextPoint=0;result.hidden=true;start.disabled=true;instructions.textContent="Select each numbered checkpoint in ascending order.";stats();tick=setInterval(()=>document.getElementById("timer").textContent=((Date.now()-started)/1000).toFixed(1),100);render();};
})();
