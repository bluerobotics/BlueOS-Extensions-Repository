import{p as X,i as W,c as v,r as B,a as P,b as $,g as se,o as ue,d as be,e as ie,f as he,h as _e,j as xe,k as Se,l as Y,m as n,n as re,t as K,q as ce,s as Ve,u as $e,v as Ie,w as de,x as G,y as J,z as Q,A as ee,B as E,C as Be,D as Te,E as we,F as Ce}from"./index.bdc38d83.js";import{u as Re,m as te,a as T,b as Ae,c as ke,d as Pe,e as ze,f as Le,g as He,h as Me,V as F,i as Ne,j as Ee}from"./color.3bb8558e.js";const O=Symbol.for("vuetify:layout"),ve=Symbol.for("vuetify:layout-item"),ne=1e3,Oe=X({overlaps:{type:Array,default:()=>[]},fullHeight:Boolean},"layout"),De=X({name:{type:String},order:{type:[Number,String],default:0},absolute:Boolean},"layout-item");function je(){const e=W(O);if(!e)throw new Error("[Vuetify] Could not find injected layout");return{getLayoutItem:e.getLayoutItem,mainRect:e.mainRect,mainStyles:e.mainStyles}}function qe(e){var c;const a=W(O);if(!a)throw new Error("[Vuetify] Could not find injected layout");const o=(c=e.id)!=null?c:`layout-item-${be()}`,t=se("useLayoutItem");ie(ve,{id:o});const l=B(!1);he(()=>l.value=!0),_e(()=>l.value=!1);const{layoutItemStyles:u,layoutItemScrimStyles:i}=a.register(t,{...e,active:v(()=>l.value?!1:e.active.value),id:o});return xe(()=>a.unregister(o)),{layoutItemStyles:u,layoutRect:a.layoutRect,layoutItemScrimStyles:i}}const Fe=(e,a,o,t)=>{let l={top:0,left:0,right:0,bottom:0};const u=[{id:"",layer:{...l}}];for(const i of e){const c=a.get(i),f=o.get(i),b=t.get(i);if(!c||!f||!b)continue;const m={...l,[c.value]:parseInt(l[c.value],10)+(b.value?parseInt(f.value,10):0)};u.push({id:i,layer:m}),l=m}return u};function Ke(e){const a=W(O,null),o=v(()=>a?a.rootZIndex.value-100:ne),t=B([]),l=P(new Map),u=P(new Map),i=P(new Map),c=P(new Map),f=P(new Map),{resizeRef:b,contentRect:m}=Re(),x=v(()=>{var s;const r=new Map,y=(s=e.overlaps)!=null?s:[];for(const _ of y.filter(d=>d.includes(":"))){const[d,g]=_.split(":");if(!t.value.includes(d)||!t.value.includes(g))continue;const I=l.get(d),R=l.get(g),A=u.get(d),N=u.get(g);!I||!R||!A||!N||(r.set(g,{position:I.value,amount:parseInt(A.value,10)}),r.set(d,{position:R.value,amount:-parseInt(N.value,10)}))}return r}),p=v(()=>{const r=[...new Set([...i.values()].map(s=>s.value))].sort((s,_)=>s-_),y=[];for(const s of r){const _=t.value.filter(d=>{var g;return((g=i.get(d))==null?void 0:g.value)===s});y.push(..._)}return Fe(y,l,u,c)}),w=v(()=>!Array.from(f.values()).some(r=>r.value)),S=v(()=>p.value[p.value.length-1].layer),z=v(()=>({"--v-layout-left":$(S.value.left),"--v-layout-right":$(S.value.right),"--v-layout-top":$(S.value.top),"--v-layout-bottom":$(S.value.bottom),...w.value?void 0:{transition:"none"}})),V=v(()=>p.value.slice(1).map((r,y)=>{let{id:s}=r;const{layer:_}=p.value[y],d=u.get(s),g=l.get(s);return{id:s,..._,size:Number(d.value),position:g.value}})),C=r=>V.value.find(y=>y.id===r),L=se("createLayout"),H=B(!1);ue(()=>{H.value=!0}),ie(O,{register:(r,y)=>{let{id:s,order:_,position:d,layoutSize:g,elementSize:I,active:R,disableTransitions:A,absolute:N}=y;i.set(s,_),l.set(s,d),u.set(s,g),c.set(s,R),A&&f.set(s,A);const oe=Se(ve,L==null?void 0:L.vnode).indexOf(r);oe>-1?t.value.splice(oe,0,s):t.value.push(s);const ae=v(()=>V.value.findIndex(k=>k.id===s)),D=v(()=>o.value+p.value.length*2-ae.value*2),pe=v(()=>{const k=d.value==="left"||d.value==="right",j=d.value==="right",ge=d.value==="bottom",le={[d.value]:0,zIndex:D.value,transform:`translate${k?"X":"Y"}(${(R.value?0:-110)*(j||ge?-1:1)}%)`,position:N.value||o.value!==ne?"absolute":"fixed",...w.value?void 0:{transition:"none"}};if(!H.value)return le;const h=V.value[ae.value];if(!h)throw new Error(`[Vuetify] Could not find layout item "${s}"`);const q=x.value.get(s);return q&&(h[q.position]+=q.amount),{...le,height:k?`calc(100% - ${h.top}px - ${h.bottom}px)`:I.value?`${I.value}px`:void 0,left:j?void 0:`${h.left}px`,right:j?`${h.right}px`:void 0,top:d.value!=="bottom"?`${h.top}px`:void 0,bottom:d.value!=="top"?`${h.bottom}px`:void 0,width:k?I.value?`${I.value}px`:void 0:`calc(100% - ${h.left}px - ${h.right}px)`}}),ye=v(()=>({zIndex:D.value-1}));return{layoutItemStyles:pe,layoutItemScrimStyles:ye,zIndex:D}},unregister:r=>{i.delete(r),l.delete(r),u.delete(r),c.delete(r),f.delete(r),t.value=t.value.filter(y=>y!==r)},mainRect:S,mainStyles:z,getLayoutItem:C,items:V,layoutRect:m,rootZIndex:o});const M=v(()=>["v-layout",{"v-layout--full-height":e.fullHeight}]),fe=v(()=>({zIndex:o.value,position:a?"relative":void 0,overflow:a?"hidden":void 0}));return{layoutClasses:M,layoutStyles:fe,getLayoutItem:C,items:V,layoutRect:m,layoutRef:b}}const U=Y()({name:"VToolbarTitle",props:{text:String,...te()},setup(e,a){let{slots:o}=a;return T(()=>{var t;const l=!!(o.default||o.text||e.text);return n(e.tag,{class:"v-toolbar-title"},{default:()=>[l&&n("div",{class:"v-toolbar-title__placeholder"},[o.text?o.text():e.text,(t=o.default)==null?void 0:t.call(o)])]})}),{}}}),Ue=[null,"prominent","default","comfortable","compact"],me=X({absolute:Boolean,collapse:Boolean,color:String,density:{type:String,default:"default",validator:e=>Ue.includes(e)},extended:Boolean,extensionHeight:{type:[Number,String],default:48},flat:Boolean,floating:Boolean,height:{type:[Number,String],default:64},image:String,title:String,...Ae(),...ke(),...Pe(),...te({tag:"header"}),...re()},"v-toolbar"),Z=Y()({name:"VToolbar",props:me(),setup(e,a){var o;let{slots:t}=a;const{backgroundColorClasses:l,backgroundColorStyles:u}=ze(K(e,"color")),{borderClasses:i}=Le(e),{elevationClasses:c}=He(e),{roundedClasses:f}=Me(e),{themeClasses:b}=ce(e),m=B(!!(e.extended||(o=t.extension)!=null&&o.call(t))),x=v(()=>parseInt(Number(e.height)+(e.density==="prominent"?Number(e.height):0)-(e.density==="comfortable"?8:0)-(e.density==="compact"?16:0),10)),p=v(()=>m.value?parseInt(Number(e.extensionHeight)+(e.density==="prominent"?Number(e.extensionHeight):0)-(e.density==="comfortable"?4:0)-(e.density==="compact"?8:0),10):0);return Ve({VBtn:{variant:"text"}}),T(()=>{var w,S,z,V,C;const L=!!(e.title||t.title),H=!!(t.image||e.image),M=(w=t.extension)==null?void 0:w.call(t);return m.value=!!(e.extended||M),n(e.tag,{class:["v-toolbar",{"v-toolbar--absolute":e.absolute,"v-toolbar--collapse":e.collapse,"v-toolbar--flat":e.flat,"v-toolbar--floating":e.floating,[`v-toolbar--density-${e.density}`]:!0},l.value,i.value,c.value,f.value,b.value],style:[u.value]},{default:()=>[H&&n("div",{key:"image",class:"v-toolbar__image"},[n(F,{defaults:{VImg:{cover:!0,src:e.image}}},{default:()=>[t.image?(S=t.image)==null?void 0:S.call(t):n(Ne,null,null)]})]),n(F,{defaults:{VTabs:{height:$(x.value)}}},{default:()=>[n("div",{class:"v-toolbar__content",style:{height:$(x.value)}},[t.prepend&&n("div",{class:"v-toolbar__prepend"},[(z=t.prepend)==null?void 0:z.call(t)]),L&&n(U,{key:"title",text:e.title},{text:t.title}),(V=t.default)==null?void 0:V.call(t),t.append&&n("div",{class:"v-toolbar__append"},[(C=t.append)==null?void 0:C.call(t)])])]}),n(F,{defaults:{VTabs:{height:$(p.value)}}},{default:()=>[n(Ee,null,{default:()=>[m.value&&n("div",{class:"v-toolbar__extension",style:{height:$(p.value)}},[M])]})]})]})}),{contentHeight:x,extensionHeight:p}}});function Ze(e){var a;return $e(e,Object.keys((a=Z==null?void 0:Z.props)!=null?a:{}))}const Xe=Y()({name:"VAppBar",props:{modelValue:{type:Boolean,default:!0},location:{type:String,default:"top",validator:e=>["top","bottom"].includes(e)},...me(),...De(),height:{type:[Number,String],default:64}},emits:{"update:modelValue":e=>!0},setup(e,a){let{slots:o}=a;const t=B(),l=Ie(e,"modelValue"),u=v(()=>{var x,p;var c,f;const b=(x=(c=t.value)==null?void 0:c.contentHeight)!=null?x:0,m=(p=(f=t.value)==null?void 0:f.extensionHeight)!=null?p:0;return b+m}),{layoutItemStyles:i}=qe({id:e.name,order:v(()=>parseInt(e.order,10)),position:K(e,"location"),layoutSize:u,elementSize:u,active:l,absolute:K(e,"absolute")});return T(()=>{const[c]=Ze(e);return n(Z,de({ref:t,class:["v-app-bar",{"v-app-bar--bottom":e.location==="bottom"}],style:{...i.value,height:void 0}},c),o)}),{}}}),We=G({name:"VAppBarTitle",props:{...U.props},setup(e,a){let{slots:o}=a;return T(()=>n(U,de(e,{class:"v-app-bar-title"}),o)),{}}}),Ye=J({__name:"AppBar",setup(e){return(a,o)=>(Q(),ee(Xe,{flat:""},{default:E(()=>[n(We,null,{default:E(()=>[Be(" BlueOS Store Apps ")]),_:1})]),_:1}))}});function Ge(){const e=B(!1);return ue(()=>{window.requestAnimationFrame(()=>{e.value=!0})}),{ssrBootStyles:v(()=>e.value?void 0:{transition:"none !important"}),isBooted:Te(e)}}const Je=G({name:"VMain",props:{scrollable:Boolean,...te({tag:"main"})},setup(e,a){let{slots:o}=a;const{mainStyles:t}=je(),{ssrBootStyles:l}=Ge();return T(()=>{var u,i;return n(e.tag,{class:["v-main",{"v-main--scrollable":e.scrollable}],style:[t.value,l.value]},{default:()=>[e.scrollable?n("div",{class:"v-main__scroller"},[(u=o.default)==null?void 0:u.call(o)]):(i=o.default)==null?void 0:i.call(o)]})}),{}}}),Qe=J({__name:"View",setup(e){return(a,o)=>{const t=we("router-view");return Q(),ee(Je,null,{default:E(()=>[n(t)]),_:1})}}});const et=G({name:"VApp",props:{...Oe({fullHeight:!0}),...re()},setup(e,a){let{slots:o}=a;const t=ce(e),{layoutClasses:l,layoutStyles:u,getLayoutItem:i,items:c,layoutRef:f}=Ke(e),{rtlClasses:b}=Ce();return T(()=>{var m;return n("div",{ref:f,class:["v-application",t.themeClasses.value,l.value,b.value],style:u.value},[n("div",{class:"v-application__wrap"},[(m=o.default)==null?void 0:m.call(o)])])}),{getLayoutItem:i,items:c,theme:t}}}),lt=J({__name:"Default",setup(e){return(a,o)=>(Q(),ee(et,null,{default:E(()=>[n(Ye),n(Qe)]),_:1}))}});export{lt as default};
