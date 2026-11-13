(() => {
const area=document.getElementById("playArea"), start=document.getElementById("start"), instructions=document.getElementById("instructions"), result=document.getElementById("result");
let running=false,started=0,tick=null,timeout=null,score=0,errors=0,attempts=0,correct=0,caught=0,missed=0,reactions=[],round=0,shownAt=0;
function stats(){document.getElementById("score").textContent=score;document.getElementById("errors").textContent=errors;}
function finish(){if(!running)return;running=false;clearInterval(tick);clearTimeout(timeout);start.disabled=false;const elapsed=(Date.now()-started)/1000,accuracy=attempts?100*correct/attempts:0,rt=reactions.length?reactions.reduce((a,b)=>a+b,0)/reactions.length:0;
 result.hidden=false;result.textContent=`Finished! Score ${score}, accuracy ${accuracy.toFixed(1)}%, average reaction ${rt.toFixed(2)}s, caught ${caught}, missed ${missed}. Saving...`;
 fetch("/save_game_result",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({game_name:"Balloon Pop",score,accuracy,reaction_time:rt,completion_time:elapsed,errors,objects_caught:caught,objects_missed:missed,path_deviation:0})}).then(r=>r.json()).then(d=>{result.textContent+=d.success?" Saved successfully.":" Could not save.";}).catch(()=>result.textContent+=" Server connection failed.");
}
function next(){if(!running)return;if(round>=10){finish();return;}round++;area.innerHTML=`<p>Balloon ${round} of 10</p>`;const delay=500+Math.random()*700;
 timeout=setTimeout(()=>{if(!running)return;area.innerHTML="<h2>Pop the balloon!</h2>";const b=document.createElement("button");b.className="ms-btn";b.style.cssText="font-size:60px;border:0;background:transparent";b.textContent="🎈";shownAt=Date.now();b.onclick=()=>{if(!running)return;clearTimeout(timeout);attempts++;correct++;caught++;score+=10;reactions.push((Date.now()-shownAt)/1000);stats();next();};area.appendChild(b);
 timeout=setTimeout(()=>{if(!running)return;attempts++;errors++;missed++;stats();next();},2200);
 },delay);}
start.onclick=()=>{running=true;started=Date.now();score=errors=attempts=correct=caught=missed=round=0;reactions=[];result.hidden=true;start.disabled=true;instructions.textContent="Click each balloon when it appears.";stats();tick=setInterval(()=>document.getElementById("timer").textContent=((Date.now()-started)/1000).toFixed(1),100);next();};
})();
