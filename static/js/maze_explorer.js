(() => {
const area=document.getElementById("playArea"), start=document.getElementById("start");
const instructions=document.getElementById("instructions"), result=document.getElementById("result");
let running=false, started=0, tick=null, score=0, errors=0, attempts=0, correct=0, moves=0;
const walls=new Set(["1,1","1,2","2,2","3,0","3,1"]), size=5;
let pos=[0,0];
function stats(){document.getElementById("score").textContent=score;document.getElementById("errors").textContent=errors;}
function button(label, cls, fn){let b=document.createElement("button");b.className="ms-btn "+(cls||"");b.textContent=label;b.onclick=fn;return b;}
function render(){
 area.innerHTML="<h4>Move one square at a time to reach 🏁</h4><div id='grid'></div>";
 const grid=area.querySelector("#grid");
 for(let r=0;r<size;r++){let row=document.createElement("div");
  for(let c=0;c<size;c++){let key=`${r},${c}`, label=walls.has(key)?"■":(pos[0]===r&&pos[1]===c?"🙂":(r===4&&c===4?"🏁":""));
   let b=button(label,walls.has(key)?"wall":"",()=>{
    if(!running)return;
    if(Math.abs(r-pos[0])+Math.abs(c-pos[1])!==1||walls.has(key)){errors++;attempts++;stats();return;}
    pos=[r,c];moves++;score++;correct++;attempts++;stats();
    if(r===4&&c===4)finish();else render();
   });
   row.appendChild(b);
  } grid.appendChild(row);
 }
}
function finish(){if(!running)return;running=false;clearInterval(tick);start.disabled=false;
 const elapsed=(Date.now()-started)/1000, accuracy=attempts?100*correct/attempts:0;
 result.hidden=false;result.textContent=`Completed! Score ${score}, accuracy ${accuracy.toFixed(1)}%, moves ${moves}, errors ${errors}, time ${elapsed.toFixed(1)} seconds. Saving result...`;
 fetch("/save_game_result",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({game_name:"Maze Explorer",score,accuracy,reaction_time:0,completion_time:elapsed,errors,objects_caught:0,objects_missed:0,path_deviation:errors})})
 .then(r=>r.json()).then(d=>{result.textContent+=d.success?" Saved successfully.":" Could not save result.";}).catch(()=>{result.textContent+=" Could not connect to server.";});
}
start.onclick=()=>{running=true;score=errors=attempts=correct=moves=0;pos=[0,0];started=Date.now();result.hidden=true;start.disabled=true;instructions.textContent="Use adjacent squares. Dark squares are blocked.";stats();tick=setInterval(()=>document.getElementById("timer").textContent=((Date.now()-started)/1000).toFixed(1),100);render();};
})();
