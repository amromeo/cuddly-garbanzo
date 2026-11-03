let olsdDirty=false;
document.addEventListener('click',function(e){if(e.target.closest('.brand')){e.preventDefault();Shiny.setInputValue('route','worklist',{priority:'event'});return;}const b=e.target.closest('[data-command]');if(b){Shiny.setInputValue('command',{action:b.dataset.command,id:b.dataset.id||'',field:b.dataset.field||'',nonce:Date.now()},{priority:'event'});}});
document.addEventListener('change',function(e){if(e.target.matches('.row-select'))Shiny.setInputValue('selected',Array.from(document.querySelectorAll('.row-select:checked'),x=>x.value),{priority:'event'});if(/^(choice_|value_|note_)/.test(e.target.name||e.target.id)){olsdDirty=true;Shiny.setInputValue('pilot_dirty',true,{priority:'event'});}});
window.addEventListener('beforeunload',e=>{if(olsdDirty){e.preventDefault();e.returnValue='';}});
window.addEventListener('popstate',()=>Shiny.setInputValue('route',location.hash.slice(1)||'worklist',{priority:'event'}));
$(document).on('shiny:connected',function(){
 Shiny.addCustomMessageHandler('route',route=>{if(location.hash!=='#'+route)history.pushState({},'','#'+route);});
 if(location.hash)Shiny.setInputValue('route',location.hash.slice(1),{priority:'event'});else history.replaceState({},'','#worklist');
 Shiny.addCustomMessageHandler('saved',unused=>{olsdDirty=false;Shiny.setInputValue('pilot_dirty',false);});
 Shiny.addCustomMessageHandler('selectRows',ids=>{if(!Array.isArray(ids))ids=[ids];document.querySelectorAll('.row-select').forEach(x=>x.checked=ids.includes(x.value));Shiny.setInputValue('selected',ids,{priority:'event'});});
});

document.addEventListener('input',function(e){if(e.target.id.startsWith('value_')){const name=e.target.id.replace('value_','choice_');const radio=document.querySelector('input[name="'+name+'"][value="custom"]');if(radio){radio.checked=true;radio.dispatchEvent(new Event('change',{bubbles:true}));}olsdDirty=true;Shiny.setInputValue('pilot_dirty',true);}});
document.addEventListener('keydown',function(e){
 if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='s'){e.preventDefault();Shiny.setInputValue('command',{action:'save',id:'',field:'',nonce:Date.now()},{priority:'event'});return;}
 if(e.ctrlKey||e.metaKey||e.altKey||/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName)||e.target.isContentEditable)return;
 if(!['1','2'].includes(e.key))return;
 const card=Array.from(document.querySelectorAll('.field-card')).find(c=>!c.querySelector('input[name^="choice_"]:checked'));
 if(!card)return;
 const choices=Array.from(card.querySelectorAll('input[name^="choice_"]')).filter(x=>['epic','olsd'].includes(x.value));
 const choice=choices[Number(e.key)-1];if(choice){e.preventDefault();choice.click();}
});
$(document).on('shiny:value',function(e){
 if(e.name!=='page')return;
 const old=document.activeElement;if(!old||old===document.body)return;
 const id=old.id,command=old.dataset.command,record=old.dataset.id,field=old.dataset.field;
 setTimeout(()=>{
  if(document.contains(old))return;
  let next=id?document.getElementById(id):null;
  if(!next&&command)next=Array.from(document.querySelectorAll('[data-command]')).find(x=>x.dataset.command===command&&x.dataset.id===record&&x.dataset.field===field);
  if(!next){next=document.querySelector('h1');if(next)next.tabIndex=-1;}
  if(next)next.focus({preventScroll:true});
 },50);
});
let olsdDialogOrigin=null;
$(document).on('show.bs.modal','.modal',function(){olsdDialogOrigin=document.activeElement;this.setAttribute('role','dialog');this.setAttribute('aria-modal','true');const title=this.querySelector('.modal-title');if(title){title.id='olsd-dialog-title';this.setAttribute('aria-labelledby',title.id);}});
$(document).on('hidden.bs.modal','.modal',function(){if(olsdDialogOrigin&&document.contains(olsdDialogOrigin))olsdDialogOrigin.focus();});
