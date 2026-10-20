"use strict";
const vf=document.getElementById("v"),kart=[...document.querySelectorAll(".step")],navA=[...document.querySelectorAll(".stepnav a")];
let aktif=-1,siap=false;
function kirim(i){if(!siap||i<0)return;vf.contentWindow.postMessage(Object.assign({tipe:"langkah"},LANGKAH[i]),"*")}
function pilih(i){if(i===aktif)return;aktif=i;kart.forEach((k,j)=>k.classList.toggle("on",j===i));navA.forEach((a,j)=>a.classList.toggle("on",j===i));
 const a=navA[i];if(a&&a.parentElement.scrollWidth>a.parentElement.clientWidth)a.parentElement.scrollLeft=a.offsetLeft-a.parentElement.clientWidth/2;kirim(i)}
addEventListener("message",e=>{if(e.data&&e.data.tipe==="siap"){siap=true;kirim(aktif<0?0:aktif)}});
// langkah aktif = kartu yang memotong garis baca (tepat di bawah penampil di ponsel, tengah layar di desktop)
const hp=()=>matchMedia("(max-width:900px)").matches,navH=()=>document.querySelector("nav.top").offsetHeight;
function atasBaca(){return hp()?navH()+document.querySelector(".stage").offsetHeight+12:navH()+16}
function garis(){return atasBaca()+120}
navA.forEach((a,j)=>a.onclick=e=>{e.preventDefault();const ke=()=>scrollTo({top:scrollY+kart[j].getBoundingClientRect().top-atasBaca(),behavior:"smooth"});ke();setTimeout(ke,900)});
function cek(){const y=garis();let best=0;for(let j=0;j<kart.length;j++){if(kart[j].getBoundingClientRect().top<=y)best=j}pilih(best)}
addEventListener("scroll",()=>requestAnimationFrame(cek),{passive:true});addEventListener("resize",cek);cek();
// centang selesai, disimpan di perangkat ini
const simpan=JSON.parse(localStorage.getItem(KUNCI)||"{}");
function hitung(){const n=Object.values(simpan).filter(Boolean).length;document.getElementById("prog").textContent=n+"/"+kart.length+" selesai";navA.forEach((a,j)=>a.classList.toggle("done",!!simpan[j]))}
kart.forEach((k,j)=>{const c=k.querySelector(".ok input");c.checked=!!simpan[j];c.onchange=()=>{simpan[j]=c.checked;localStorage.setItem(KUNCI,JSON.stringify(simpan));hitung()}});hitung();
