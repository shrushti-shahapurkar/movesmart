(() => {
const area=document.getElementById("playArea"), start=document.getElementById("start"), instructions=document.getElementById("instructions"), result=document.getElementById("result");
const shapes=["●","▲","■","★","◆"];let running=false,started=0,tick=null,score=0,errors=0,attempts=0,correct=0,reactions=[],round=0,shownAt=0;
function stats(){document.getElementById("score").textContent=score;document.getElementById("errors").textContent=errors;}
function btn(label,fn){let b=document.createElement("button");b.className="ms-btn";b.textContent=label;b.onclick=fn;return b;}
function next(){if(!running)return;if(round>=10){finish();return;}round++;const target=shapes[Math.floor(Math.random()*shapes.length)];shownAt=Date.now();area.innerHTML=`<h3>Choose the matching shape</h3><div class="display-3">${target}</div>`;
 [...shapes].sort(()=>Math.random()-.5).forEach(s=>area.appendChild(btn(s,()=>{if(!running)return;attempts++;if(s===target){score+=10;correct++;reactions.push((Date.now()-shownAt)/1000);}else errors++;stats();next();})));
}
function finish(){if(!running)return;running=false;clearInterval(tick);start.disabled=false;const elapsed=(Date.now()-started)/1000,accuracy=attempts?100*correct/attempts:0,rt=reactions.length?reactions.reduce((a,b)=>a+b,0)/reactions.length:0;
 result.hidden=false;result.textContent=`Finished! Score ${score}, accuracy ${accuracy.toFixed(1)}%, average response ${rt.toFixed(2)}s, errors ${errors}. Saving...`;
 fetch("/save_game_result",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({game_name:"Shape Matcher",score,accuracy,reaction_time:rt,completion_time:elapsed,errors,objects_caught:0,objects_missed:0,path_deviation:0})}).then(r=>r.json()).then(d=>{result.textContent+=d.success?" Saved successfully.":" Could not save.";}).catch(()=>result.textContent+=" Server connection failed.");
}
start.onclick=()=>{running=true;started=Date.now();score=errors=attempts=correct=round=0;reactions=[];result.hidden=true;start.disabled=true;instructions.textContent="Select the same shape as the target.";stats();tick=setInterval(()=>document.getElementById("timer").textContent=((Date.now()-started)/1000).toFixed(1),100);next();};
})();
