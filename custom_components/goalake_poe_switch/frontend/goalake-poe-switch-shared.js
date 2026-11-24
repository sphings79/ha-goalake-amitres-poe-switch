/**
 * @license
 * Copyright 2019 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const R=globalThis,W=R.ShadowRoot&&(R.ShadyCSS===void 0||R.ShadyCSS.nativeShadow)&&"adoptedStyleSheets"in Document.prototype&&"replace"in CSSStyleSheet.prototype,F=Symbol(),Y=new WeakMap;let le=class{constructor(e,t,r){if(this._$cssResult$=!0,r!==F)throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");this.cssText=e,this.t=t}get styleSheet(){let e=this.o;const t=this.t;if(W&&e===void 0){const r=t!==void 0&&t.length===1;r&&(e=Y.get(t)),e===void 0&&((this.o=e=new CSSStyleSheet).replaceSync(this.cssText),r&&Y.set(t,e))}return e}toString(){return this.cssText}};const $e=s=>new le(typeof s=="string"?s:s+"",void 0,F),B=(s,...e)=>{const t=s.length===1?s[0]:e.reduce((r,o,n)=>r+(a=>{if(a._$cssResult$===!0)return a.cssText;if(typeof a=="number")return a;throw Error("Value passed to 'css' function must be a 'css' function result: "+a+". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.")})(o)+s[n+1],s[0]);return new le(t,s,F)},ve=(s,e)=>{if(W)s.adoptedStyleSheets=e.map(t=>t instanceof CSSStyleSheet?t:t.styleSheet);else for(const t of e){const r=document.createElement("style"),o=R.litNonce;o!==void 0&&r.setAttribute("nonce",o),r.textContent=t.cssText,s.appendChild(r)}},Q=W?s=>s:s=>s instanceof CSSStyleSheet?(e=>{let t="";for(const r of e.cssRules)t+=r.cssText;return $e(t)})(s):s;/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const{is:_e,defineProperty:ye,getOwnPropertyDescriptor:we,getOwnPropertyNames:Ae,getOwnPropertySymbols:xe,getPrototypeOf:Ee}=Object,I=globalThis,X=I.trustedTypes,Se=X?X.emptyScript:"",ke=I.reactiveElementPolyfillSupport,C=(s,e)=>s,D={toAttribute(s,e){switch(e){case Boolean:s=s?Se:null;break;case Object:case Array:s=s==null?s:JSON.stringify(s)}return s},fromAttribute(s,e){let t=s;switch(e){case Boolean:t=s!==null;break;case Number:t=s===null?null:Number(s);break;case Object:case Array:try{t=JSON.parse(s)}catch{t=null}}return t}},G=(s,e)=>!_e(s,e),ee={attribute:!0,type:String,converter:D,reflect:!1,useDefault:!1,hasChanged:G};Symbol.metadata??=Symbol("metadata"),I.litPropertyMetadata??=new WeakMap;let A=class extends HTMLElement{static addInitializer(e){this._$Ei(),(this.l??=[]).push(e)}static get observedAttributes(){return this.finalize(),this._$Eh&&[...this._$Eh.keys()]}static createProperty(e,t=ee){if(t.state&&(t.attribute=!1),this._$Ei(),this.prototype.hasOwnProperty(e)&&((t=Object.create(t)).wrapped=!0),this.elementProperties.set(e,t),!t.noAccessor){const r=Symbol(),o=this.getPropertyDescriptor(e,r,t);o!==void 0&&ye(this.prototype,e,o)}}static getPropertyDescriptor(e,t,r){const{get:o,set:n}=we(this.prototype,e)??{get(){return this[t]},set(a){this[t]=a}};return{get:o,set(a){const c=o?.call(this);n?.call(this,a),this.requestUpdate(e,c,r)},configurable:!0,enumerable:!0}}static getPropertyOptions(e){return this.elementProperties.get(e)??ee}static _$Ei(){if(this.hasOwnProperty(C("elementProperties")))return;const e=Ee(this);e.finalize(),e.l!==void 0&&(this.l=[...e.l]),this.elementProperties=new Map(e.elementProperties)}static finalize(){if(this.hasOwnProperty(C("finalized")))return;if(this.finalized=!0,this._$Ei(),this.hasOwnProperty(C("properties"))){const t=this.properties,r=[...Ae(t),...xe(t)];for(const o of r)this.createProperty(o,t[o])}const e=this[Symbol.metadata];if(e!==null){const t=litPropertyMetadata.get(e);if(t!==void 0)for(const[r,o]of t)this.elementProperties.set(r,o)}this._$Eh=new Map;for(const[t,r]of this.elementProperties){const o=this._$Eu(t,r);o!==void 0&&this._$Eh.set(o,t)}this.elementStyles=this.finalizeStyles(this.styles)}static finalizeStyles(e){const t=[];if(Array.isArray(e)){const r=new Set(e.flat(1/0).reverse());for(const o of r)t.unshift(Q(o))}else e!==void 0&&t.push(Q(e));return t}static _$Eu(e,t){const r=t.attribute;return r===!1?void 0:typeof r=="string"?r:typeof e=="string"?e.toLowerCase():void 0}constructor(){super(),this._$Ep=void 0,this.isUpdatePending=!1,this.hasUpdated=!1,this._$Em=null,this._$Ev()}_$Ev(){this._$ES=new Promise(e=>this.enableUpdating=e),this._$AL=new Map,this._$E_(),this.requestUpdate(),this.constructor.l?.forEach(e=>e(this))}addController(e){(this._$EO??=new Set).add(e),this.renderRoot!==void 0&&this.isConnected&&e.hostConnected?.()}removeController(e){this._$EO?.delete(e)}_$E_(){const e=new Map,t=this.constructor.elementProperties;for(const r of t.keys())this.hasOwnProperty(r)&&(e.set(r,this[r]),delete this[r]);e.size>0&&(this._$Ep=e)}createRenderRoot(){const e=this.shadowRoot??this.attachShadow(this.constructor.shadowRootOptions);return ve(e,this.constructor.elementStyles),e}connectedCallback(){this.renderRoot??=this.createRenderRoot(),this.enableUpdating(!0),this._$EO?.forEach(e=>e.hostConnected?.())}enableUpdating(e){}disconnectedCallback(){this._$EO?.forEach(e=>e.hostDisconnected?.())}attributeChangedCallback(e,t,r){this._$AK(e,r)}_$ET(e,t){const r=this.constructor.elementProperties.get(e),o=this.constructor._$Eu(e,r);if(o!==void 0&&r.reflect===!0){const n=(r.converter?.toAttribute!==void 0?r.converter:D).toAttribute(t,r.type);this._$Em=e,n==null?this.removeAttribute(o):this.setAttribute(o,n),this._$Em=null}}_$AK(e,t){const r=this.constructor,o=r._$Eh.get(e);if(o!==void 0&&this._$Em!==o){const n=r.getPropertyOptions(o),a=typeof n.converter=="function"?{fromAttribute:n.converter}:n.converter?.fromAttribute!==void 0?n.converter:D;this._$Em=o;const c=a.fromAttribute(t,n.type);this[o]=c??this._$Ej?.get(o)??c,this._$Em=null}}requestUpdate(e,t,r,o=!1,n){if(e!==void 0){const a=this.constructor;if(o===!1&&(n=this[e]),r??=a.getPropertyOptions(e),!((r.hasChanged??G)(n,t)||r.useDefault&&r.reflect&&n===this._$Ej?.get(e)&&!this.hasAttribute(a._$Eu(e,r))))return;this.C(e,t,r)}this.isUpdatePending===!1&&(this._$ES=this._$EP())}C(e,t,{useDefault:r,reflect:o,wrapped:n},a){r&&!(this._$Ej??=new Map).has(e)&&(this._$Ej.set(e,a??t??this[e]),n!==!0||a!==void 0)||(this._$AL.has(e)||(this.hasUpdated||r||(t=void 0),this._$AL.set(e,t)),o===!0&&this._$Em!==e&&(this._$Eq??=new Set).add(e))}async _$EP(){this.isUpdatePending=!0;try{await this._$ES}catch(t){Promise.reject(t)}const e=this.scheduleUpdate();return e!=null&&await e,!this.isUpdatePending}scheduleUpdate(){return this.performUpdate()}performUpdate(){if(!this.isUpdatePending)return;if(!this.hasUpdated){if(this.renderRoot??=this.createRenderRoot(),this._$Ep){for(const[o,n]of this._$Ep)this[o]=n;this._$Ep=void 0}const r=this.constructor.elementProperties;if(r.size>0)for(const[o,n]of r){const{wrapped:a}=n,c=this[o];a!==!0||this._$AL.has(o)||c===void 0||this.C(o,void 0,n,c)}}let e=!1;const t=this._$AL;try{e=this.shouldUpdate(t),e?(this.willUpdate(t),this._$EO?.forEach(r=>r.hostUpdate?.()),this.update(t)):this._$EM()}catch(r){throw e=!1,this._$EM(),r}e&&this._$AE(t)}willUpdate(e){}_$AE(e){this._$EO?.forEach(t=>t.hostUpdated?.()),this.hasUpdated||(this.hasUpdated=!0,this.firstUpdated(e)),this.updated(e)}_$EM(){this._$AL=new Map,this.isUpdatePending=!1}get updateComplete(){return this.getUpdateComplete()}getUpdateComplete(){return this._$ES}shouldUpdate(e){return!0}update(e){this._$Eq&&=this._$Eq.forEach(t=>this._$ET(t,this[t])),this._$EM()}updated(e){}firstUpdated(e){}};A.elementStyles=[],A.shadowRootOptions={mode:"open"},A[C("elementProperties")]=new Map,A[C("finalized")]=new Map,ke?.({ReactiveElement:A}),(I.reactiveElementVersions??=[]).push("2.1.2");/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const K=globalThis,te=s=>s,j=K.trustedTypes,re=j?j.createPolicy("lit-html",{createHTML:s=>s}):void 0,fe="$lit$",m=`lit$${Math.random().toFixed(9).slice(2)}$`,pe="?"+m,Pe=`<${pe}>`,_=document,O=()=>_.createComment(""),M=s=>s===null||typeof s!="object"&&typeof s!="function",Z=Array.isArray,Ce=s=>Z(s)||typeof s?.[Symbol.iterator]=="function",V=`[ 	
\f\r]`,P=/<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g,se=/-->/g,oe=/>/g,$=RegExp(`>|${V}(?:([^\\s"'>=/]+)(${V}*=${V}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`,"g"),ne=/'/g,ae=/"/g,he=/^(?:script|style|textarea|title)$/i,Oe=s=>(e,...t)=>({_$litType$:s,strings:e,values:t}),L=Oe(1),E=Symbol.for("lit-noChange"),h=Symbol.for("lit-nothing"),ie=new WeakMap,v=_.createTreeWalker(_,129);function ue(s,e){if(!Z(s)||!s.hasOwnProperty("raw"))throw Error("invalid template strings array");return re!==void 0?re.createHTML(e):e}const Me=(s,e)=>{const t=s.length-1,r=[];let o,n=e===2?"<svg>":e===3?"<math>":"",a=P;for(let c=0;c<t;c++){const i=s[c];let l,f,d=-1,p=0;for(;p<i.length&&(a.lastIndex=p,f=a.exec(i),f!==null);)p=a.lastIndex,a===P?f[1]==="!--"?a=se:f[1]!==void 0?a=oe:f[2]!==void 0?(he.test(f[2])&&(o=RegExp("</"+f[2],"g")),a=$):f[3]!==void 0&&(a=$):a===$?f[0]===">"?(a=o??P,d=-1):f[1]===void 0?d=-2:(d=a.lastIndex-f[2].length,l=f[1],a=f[3]===void 0?$:f[3]==='"'?ae:ne):a===ae||a===ne?a=$:a===se||a===oe?a=P:(a=$,o=void 0);const u=a===$&&s[c+1].startsWith("/>")?" ":"";n+=a===P?i+Pe:d>=0?(r.push(l),i.slice(0,d)+fe+i.slice(d)+m+u):i+m+(d===-2?c:u)}return[ue(s,n+(s[t]||"<?>")+(e===2?"</svg>":e===3?"</math>":"")),r]};class U{constructor({strings:e,_$litType$:t},r){let o;this.parts=[];let n=0,a=0;const c=e.length-1,i=this.parts,[l,f]=Me(e,t);if(this.el=U.createElement(l,r),v.currentNode=this.el.content,t===2||t===3){const d=this.el.content.firstChild;d.replaceWith(...d.childNodes)}for(;(o=v.nextNode())!==null&&i.length<c;){if(o.nodeType===1){if(o.hasAttributes())for(const d of o.getAttributeNames())if(d.endsWith(fe)){const p=f[a++],u=o.getAttribute(d).split(m),w=/([.?@])?(.*)/.exec(p);i.push({type:1,index:n,name:w[2],strings:u,ctor:w[1]==="."?Te:w[1]==="?"?Ne:w[1]==="@"?He:q}),o.removeAttribute(d)}else d.startsWith(m)&&(i.push({type:6,index:n}),o.removeAttribute(d));if(he.test(o.tagName)){const d=o.textContent.split(m),p=d.length-1;if(p>0){o.textContent=j?j.emptyScript:"";for(let u=0;u<p;u++)o.append(d[u],O()),v.nextNode(),i.push({type:2,index:++n});o.append(d[p],O())}}}else if(o.nodeType===8)if(o.data===pe)i.push({type:2,index:n});else{let d=-1;for(;(d=o.data.indexOf(m,d+1))!==-1;)i.push({type:7,index:n}),d+=m.length-1}n++}}static createElement(e,t){const r=_.createElement("template");return r.innerHTML=e,r}}function S(s,e,t=s,r){if(e===E)return e;let o=r!==void 0?t._$Co?.[r]:t._$Cl;const n=M(e)?void 0:e._$litDirective$;return o?.constructor!==n&&(o?._$AO?.(!1),n===void 0?o=void 0:(o=new n(s),o._$AT(s,t,r)),r!==void 0?(t._$Co??=[])[r]=o:t._$Cl=o),o!==void 0&&(e=S(s,o._$AS(s,e.values),o,r)),e}class Ue{constructor(e,t){this._$AV=[],this._$AN=void 0,this._$AD=e,this._$AM=t}get parentNode(){return this._$AM.parentNode}get _$AU(){return this._$AM._$AU}u(e){const{el:{content:t},parts:r}=this._$AD,o=(e?.creationScope??_).importNode(t,!0);v.currentNode=o;let n=v.nextNode(),a=0,c=0,i=r[0];for(;i!==void 0;){if(a===i.index){let l;i.type===2?l=new T(n,n.nextSibling,this,e):i.type===1?l=new i.ctor(n,i.name,i.strings,this,e):i.type===6&&(l=new Re(n,this,e)),this._$AV.push(l),i=r[++c]}a!==i?.index&&(n=v.nextNode(),a++)}return v.currentNode=_,o}p(e){let t=0;for(const r of this._$AV)r!==void 0&&(r.strings!==void 0?(r._$AI(e,r,t),t+=r.strings.length-2):r._$AI(e[t])),t++}}class T{get _$AU(){return this._$AM?._$AU??this._$Cv}constructor(e,t,r,o){this.type=2,this._$AH=h,this._$AN=void 0,this._$AA=e,this._$AB=t,this._$AM=r,this.options=o,this._$Cv=o?.isConnected??!0}get parentNode(){let e=this._$AA.parentNode;const t=this._$AM;return t!==void 0&&e?.nodeType===11&&(e=t.parentNode),e}get startNode(){return this._$AA}get endNode(){return this._$AB}_$AI(e,t=this){e=S(this,e,t),M(e)?e===h||e==null||e===""?(this._$AH!==h&&this._$AR(),this._$AH=h):e!==this._$AH&&e!==E&&this._(e):e._$litType$!==void 0?this.$(e):e.nodeType!==void 0?this.T(e):Ce(e)?this.k(e):this._(e)}O(e){return this._$AA.parentNode.insertBefore(e,this._$AB)}T(e){this._$AH!==e&&(this._$AR(),this._$AH=this.O(e))}_(e){this._$AH!==h&&M(this._$AH)?this._$AA.nextSibling.data=e:this.T(_.createTextNode(e)),this._$AH=e}$(e){const{values:t,_$litType$:r}=e,o=typeof r=="number"?this._$AC(e):(r.el===void 0&&(r.el=U.createElement(ue(r.h,r.h[0]),this.options)),r);if(this._$AH?._$AD===o)this._$AH.p(t);else{const n=new Ue(o,this),a=n.u(this.options);n.p(t),this.T(a),this._$AH=n}}_$AC(e){let t=ie.get(e.strings);return t===void 0&&ie.set(e.strings,t=new U(e)),t}k(e){Z(this._$AH)||(this._$AH=[],this._$AR());const t=this._$AH;let r,o=0;for(const n of e)o===t.length?t.push(r=new T(this.O(O()),this.O(O()),this,this.options)):r=t[o],r._$AI(n),o++;o<t.length&&(this._$AR(r&&r._$AB.nextSibling,o),t.length=o)}_$AR(e=this._$AA.nextSibling,t){for(this._$AP?.(!1,!0,t);e!==this._$AB;){const r=te(e).nextSibling;te(e).remove(),e=r}}setConnected(e){this._$AM===void 0&&(this._$Cv=e,this._$AP?.(e))}}class q{get tagName(){return this.element.tagName}get _$AU(){return this._$AM._$AU}constructor(e,t,r,o,n){this.type=1,this._$AH=h,this._$AN=void 0,this.element=e,this.name=t,this._$AM=o,this.options=n,r.length>2||r[0]!==""||r[1]!==""?(this._$AH=Array(r.length-1).fill(new String),this.strings=r):this._$AH=h}_$AI(e,t=this,r,o){const n=this.strings;let a=!1;if(n===void 0)e=S(this,e,t,0),a=!M(e)||e!==this._$AH&&e!==E,a&&(this._$AH=e);else{const c=e;let i,l;for(e=n[0],i=0;i<n.length-1;i++)l=S(this,c[r+i],t,i),l===E&&(l=this._$AH[i]),a||=!M(l)||l!==this._$AH[i],l===h?e=h:e!==h&&(e+=(l??"")+n[i+1]),this._$AH[i]=l}a&&!o&&this.j(e)}j(e){e===h?this.element.removeAttribute(this.name):this.element.setAttribute(this.name,e??"")}}class Te extends q{constructor(){super(...arguments),this.type=3}j(e){this.element[this.name]=e===h?void 0:e}}class Ne extends q{constructor(){super(...arguments),this.type=4}j(e){this.element.toggleAttribute(this.name,!!e&&e!==h)}}class He extends q{constructor(e,t,r,o,n){super(e,t,r,o,n),this.type=5}_$AI(e,t=this){if((e=S(this,e,t,0)??h)===E)return;const r=this._$AH,o=e===h&&r!==h||e.capture!==r.capture||e.once!==r.once||e.passive!==r.passive,n=e!==h&&(r===h||o);o&&this.element.removeEventListener(this.name,this,r),n&&this.element.addEventListener(this.name,this,e),this._$AH=e}handleEvent(e){typeof this._$AH=="function"?this._$AH.call(this.options?.host??this.element,e):this._$AH.handleEvent(e)}}class Re{constructor(e,t,r){this.element=e,this.type=6,this._$AN=void 0,this._$AM=t,this.options=r}get _$AU(){return this._$AM._$AU}_$AI(e){S(this,e)}}const Le=K.litHtmlPolyfillSupport;Le?.(U,T),(K.litHtmlVersions??=[]).push("3.3.3");const De=(s,e,t)=>{const r=t?.renderBefore??e;let o=r._$litPart$;if(o===void 0){const n=t?.renderBefore??null;r._$litPart$=o=new T(e.insertBefore(O(),n),n,void 0,t??{})}return o._$AI(s),o};/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const J=globalThis;class x extends A{constructor(){super(...arguments),this.renderOptions={host:this},this._$Do=void 0}createRenderRoot(){const e=super.createRenderRoot();return this.renderOptions.renderBefore??=e.firstChild,e}update(e){const t=this.render();this.hasUpdated||(this.renderOptions.isConnected=this.isConnected),super.update(e),this._$Do=De(t,this.renderRoot,this.renderOptions)}connectedCallback(){super.connectedCallback(),this._$Do?.setConnected(!0)}disconnectedCallback(){super.disconnectedCallback(),this._$Do?.setConnected(!1)}render(){return E}}x._$litElement$=!0,x.finalized=!0,J.litElementHydrateSupport?.({LitElement:x});const je=J.litElementPolyfillSupport;je?.({LitElement:x});(J.litElementVersions??=[]).push("4.2.2");/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */const ze={attribute:!0,type:String,converter:D,reflect:!1,hasChanged:G},Be=(s=ze,e,t)=>{const{kind:r,metadata:o}=t;let n=globalThis.litPropertyMetadata.get(o);if(n===void 0&&globalThis.litPropertyMetadata.set(o,n=new Map),r==="setter"&&((s=Object.create(s)).wrapped=!0),n.set(t.name,s),r==="accessor"){const{name:a}=t;return{set(c){const i=e.get.call(this);e.set.call(this,c),this.requestUpdate(a,i,s,!0,c)},init(c){return c!==void 0&&this.C(a,void 0,s,c),c}}}if(r==="setter"){const{name:a}=t;return function(c){const i=this[a];e.call(this,c),this.requestUpdate(a,i,s,!0,c)}}throw Error("Unsupported decorator location: "+r)};function g(s){return(e,t)=>typeof t=="object"?Be(s,e,t):((r,o,n)=>{const a=o.hasOwnProperty(n);return o.constructor.createProperty(n,r),a?Object.getOwnPropertyDescriptor(o,n):void 0})(s,e,t)}/**
 * @license
 * Copyright 2017 Google LLC
 * SPDX-License-Identifier: BSD-3-Clause
 */function et(s){return g({...s,state:!0,attribute:!1})}function ge(s){return e=>{customElements.get(s)||customElements.define(s,e)}}var Ie=Object.defineProperty,qe=Object.getOwnPropertyDescriptor,k=(s,e,t,r)=>{for(var o=r>1?void 0:r?qe(e,t):e,n=s.length-1,a;n>=0;n--)(a=s[n])&&(o=(r?a(e,t,o):a(o))||o);return r&&o&&Ie(e,t,o),o};let b=class extends x{constructor(){super(...arguments),this.open=!1,this.heading="",this.message="",this.okLabel="OK",this.cancelLabel="Cancel"}render(){return L`<div class="dialog" role="alertdialog" aria-modal="true">
      <h3>${this.heading}</h3>
      <p>${this.message}</p>
      <div class="actions">
        <button @click=${()=>this.dispatchEvent(new CustomEvent("cancel"))}>${this.cancelLabel}</button>
        <button class="ok" @click=${()=>this.dispatchEvent(new CustomEvent("confirm"))}>${this.okLabel}</button>
      </div>
    </div>`}};b.styles=B`
    :host {
      display: none;
    }
    :host([open]) {
      display: flex;
      position: fixed;
      inset: 0;
      z-index: 20;
      align-items: center;
      justify-content: center;
      background: rgba(0, 0, 0, 0.55);
      padding: 16px;
    }
    .dialog {
      max-width: 420px;
      width: 100%;
      background: var(--gp-surface, #0b131d);
      color: var(--gp-fg, #dff2f6);
      border: 1px solid var(--gp-warn, #ffb020);
      border-radius: 12px;
      padding: 20px;
      font-family: var(--gp-sans, system-ui);
    }
    h3 {
      margin: 0 0 8px;
      color: var(--gp-warn, #ffb020);
    }
    p {
      margin: 0 0 18px;
      line-height: 1.5;
    }
    .actions {
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }
    button {
      font: inherit;
      color: inherit;
      border-radius: 8px;
      padding: 7px 16px;
      border: 1px solid var(--gp-line, #1b2b3d);
      background: var(--gp-surface-2, #101b28);
      cursor: pointer;
    }
    button.ok {
      background: var(--gp-crit, #ff4d5e);
      border-color: var(--gp-crit, #ff4d5e);
      color: #fff;
    }
  `;k([g({type:Boolean,reflect:!0})],b.prototype,"open",2);k([g()],b.prototype,"heading",2);k([g()],b.prototype,"message",2);k([g()],b.prototype,"okLabel",2);k([g()],b.prototype,"cancelLabel",2);b=k([ge("gp-confirm")],b);function Ve(s){return s==null?"–":`${s.toFixed(s>=10?1:2)} W`}function tt(s){return s?s>=1e3?`${(s/1e3).toFixed(1)} Mbit/s`:`${s} kbit/s`:"–"}function rt(s){return s?`${s} Mbit/s`:"–"}var We=Object.defineProperty,Fe=Object.getOwnPropertyDescriptor,N=(s,e,t,r)=>{for(var o=r>1?void 0:r?Fe(e,t):e,n=s.length-1,a;n>=0;n--)(a=s[n])&&(o=(r?a(e,t,o):a(o))||o);return r&&o&&We(e,t,o),o};let y=class extends x{constructor(){super(...arguments),this.ports=[],this.selected=null,this.compact=!1,this.readonly=!1}_ordered(){const s=this.ports.filter(t=>t.is_poe).sort((t,r)=>Number(t.label)-Number(r.label)),e=this.ports.filter(t=>!t.is_poe).sort((t,r)=>t.label.localeCompare(r.label));return[...s,...e]}render(){const s=this._ordered(),e=s.findIndex(t=>!t.is_poe);return L`<div class="rack">
      ${s.map((t,r)=>L`${r===e&&r>0?L`<span class="gap"></span>`:""}
          <button
            class="port ${t.connected?"linked":""} ${t.is_poe&&t.power_w?"poe-on":""} ${t.is_poe&&t.poe_enabled===!1?"poe-off":""} ${this.selected===t.index?"selected":""}"
            title="${t.label}"
            @click=${()=>!this.readonly&&this.dispatchEvent(new CustomEvent("port-select",{detail:t.index}))}
          >
            <span class="led"></span>
            <span class="num">${t.label}</span>
            <span class="sub">${t.is_poe?t.power_w?Ve(t.power_w):"":t.connected?`${t.speed_mbps}M`:""}</span>
          </button>`)}
    </div>`}};y.styles=B`
    :host {
      display: block;
    }
    .rack {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      align-items: stretch;
    }
    .gap {
      width: 10px;
    }
    button.port {
      font: inherit;
      color: var(--gp-fg, #dff2f6);
      background: var(--gp-inset, #0d1723);
      border: 1px solid var(--gp-line, #1b2b3d);
      border-radius: 8px;
      min-width: 56px;
      padding: 8px 4px 7px;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 4px;
      position: relative;
    }
    :host([compact]) button.port {
      min-width: 0;
      width: 21px;
      height: 21px;
      padding: 0;
      border-radius: 5px;
    }
    button.port:hover {
      border-color: var(--gp-accent, #2ae6dc);
    }
    :host([readonly]) button.port {
      cursor: default;
    }
    :host([readonly]) button.port:hover:not(.selected) {
      border-color: var(--gp-line, #1b2b3d);
    }
    button.port.selected {
      border-color: var(--gp-accent, #2ae6dc);
      box-shadow: 0 0 0 1px var(--gp-accent, #2ae6dc);
    }
    .led {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      background: var(--gp-track, #132434);
    }
    .linked .led {
      background: var(--gp-ok, #35d67a);
      box-shadow: 0 0 6px var(--gp-ok, #35d67a);
    }
    .poe-on .led {
      background: var(--gp-accent, #2ae6dc);
      box-shadow: 0 0 6px var(--gp-accent, #2ae6dc);
    }
    .poe-off {
      border-style: dashed !important;
      border-color: var(--gp-crit, #ff4d5e) !important;
    }
    .num {
      font-family: var(--gp-mono, monospace);
      font-weight: 600;
      font-size: 13px;
    }
    .sub {
      font-family: var(--gp-mono, monospace);
      font-size: 10px;
      color: var(--gp-dim, #5d7d92);
      min-height: 13px;
    }
    :host([compact]) .num,
    :host([compact]) .sub {
      display: none;
    }
    :host([compact]) .led {
      margin: auto;
    }
  `;N([g({attribute:!1})],y.prototype,"ports",2);N([g({type:Number})],y.prototype,"selected",2);N([g({type:Boolean})],y.prototype,"compact",2);N([g({type:Boolean,reflect:!0})],y.prototype,"readonly",2);y=N([ge("gp-port-grid")],y);const Ge="modulepreload",Ke=function(s){return"/"+s},ce={},Ze=function(e,t,r){let o=Promise.resolve();if(t&&t.length>0){let a=function(l){return Promise.all(l.map(f=>Promise.resolve(f).then(d=>({status:"fulfilled",value:d}),d=>({status:"rejected",reason:d}))))};document.getElementsByTagName("link");const c=document.querySelector("meta[property=csp-nonce]"),i=c?.nonce||c?.getAttribute("nonce");o=a(t.map(l=>{if(l=Ke(l),l in ce)return;ce[l]=!0;const f=l.endsWith(".css"),d=f?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${l}"]${d}`))return;const p=document.createElement("link");if(p.rel=f?"stylesheet":Ge,f||(p.as="script"),p.crossOrigin="",p.href=l,i&&p.setAttribute("nonce",i),document.head.appendChild(p),f)return new Promise((u,w)=>{p.addEventListener("load",u),p.addEventListener("error",()=>w(new Error(`Unable to preload CSS for ${l}`)))})}))}function n(a){const c=new Event("vite:preloadError",{cancelable:!0});if(c.payload=a,window.dispatchEvent(c),!c.defaultPrevented)throw a}return o.then(a=>{for(const c of a||[])c.status==="rejected"&&n(c.reason);return e().catch(n)})},z={"app.title":"PoE Switch","nav.overview":"Overview","nav.device":"Switch","nav.settings":"Settings","state.online":"Online","state.offline":"Not reachable","state.on":"On","state.off":"Off","overview.empty":"No switch is set up yet. Add one under Settings → Devices & services.","overview.total_power":"Total PoE power","overview.switches":"Switches","overview.ports_linked":"{n} of {m} ports linked","stat.voltage":"Supply voltage","stat.power":"PoE power","stat.temperature":"Temperature","stat.firmware":"Firmware","stat.cloud":"Cloud","stat.cloud_on":"Connected","stat.cloud_off":"Not connected","port.title":"Port {port}","port.hint":"Select a port to see details.","port.link":"Link","port.no_link":"No link","port.power":"PoE power","port.tx":"Transmit","port.rx":"Receive","port.poe":"PoE","port.extend":"Extend (10 Mbit/s, for long cables)","port.mode":"Mode","port.priority":"Priority (0–6)","port.limit_up":"Upload limit (Mbit/s, 0 = none)","port.limit_down":"Download limit (Mbit/s, 0 = none)","port.flow":"Flow control","port.restart":"Restart port","port.uplink_note":"Uplink ports are read-only: a change could cut the connection to the switch.","port.apply":"Apply","mode.down":"Down","mode.10m_half":"10M half duplex","mode.10m_full":"10M full duplex","mode.100m_half":"100M half duplex","mode.100m_full":"100M full duplex","mode.1000m_full":"1000M full duplex","admin.required":"Changing settings needs administrator rights.","settings.appearance":"Appearance","settings.palette":"Colour scheme","settings.mode":"Light or dark","settings.mode.auto":"Follow Home Assistant","settings.mode.dark":"Dark","settings.mode.light":"Light","settings.language":"Language","settings.language.auto":"Follow Home Assistant","settings.features":"Switch features","feature.lldp":"LLDP","feature.storm":"Storm control","feature.watchdog":"PoE watchdog","feature.ai_auto_extend":"PoE auto extend","feature.power_warn":"Total power warning (W)","settings.maintenance":"Maintenance","settings.reboot":"Reboot switch","confirm.title":"Please confirm","confirm.ok":"Yes, do it","confirm.cancel":"Cancel","confirm.reboot":"The switch restarts and every connected PoE device loses power for about a minute. Continue?","confirm.restart_port":"The device on port {port} loses power for a few seconds. Continue?","confirm.poe_off":"Switching PoE off on port {port} cuts the power of the connected device. Continue?","error.write":"The change was not applied: {message}","error.load":"Could not load the data: {message}","card.device":"Switch","card.title":"Title (optional)","card.ports":"Ports shown","card.interactive":"Allow switching PoE (administrators only)","card.scheme":"Colour scheme","card.no_device":"No switch found. Set one up first.","card.pick":"Choose a switch in the card editor.","card.description":"Ports, power and PoE control of a Goalake / Amitres PoE switch"},me={de:()=>Ze(()=>import("./goalake-poe-switch-lang-de.js"),[]).then(s=>s.de)},st=["en",...Object.keys(me)].sort(),H={en:z},Je=s=>(s||"en").split("-")[0].toLowerCase();async function ot(s){const e=Je(s);if(H[e])return H[e];const t=me[e];if(!t)return z;try{return H[e]=await t(),H[e]}catch{return z}}function nt(s,e,t){let r=s[e]??z[e]??e;if(t)for(const[o,n]of Object.entries(t))r=r.replace(`{${o}}`,String(n));return r}const de=[{id:"reactor",name:"Reactor",dark:{bg:"#05090f",surface:"#0b131d","surface-2":"#101b28",inset:"#0d1723",line:"#1b2b3d","line-soft":"#152435",fg:"#dff2f6","fg-2":"#9fb8c6",dim:"#5d7d92",accent:"#2ae6dc","accent-deep":"#1b8fd6","accent-wash":"#0e2b30",magenta:"#ff3ea5","magenta-wash":"#2a0d1e",ok:"#35d67a",warn:"#ffb020",crit:"#ff4d5e",track:"#132434","on-accent":"#04141a"},light:{bg:"#eef2f6",surface:"#ffffff","surface-2":"#f6f9fb",inset:"#e8eef3",line:"#cbd8e2","line-soft":"#dfe7ee",fg:"#0c1a24","fg-2":"#3a5162",dim:"#5b7484",accent:"#0c847e","accent-deep":"#0f5f8c","accent-wash":"#d9f0ee",magenta:"#b4176e","magenta-wash":"#fbe4f0",ok:"#0f7a44",warn:"#8a5804",crit:"#b52436",track:"#dae3ea","on-accent":"#ffffff"}},{id:"cockpit",name:"Cockpit",dark:{bg:"#0a0704",surface:"#14100a","surface-2":"#1c1710",inset:"#17120b",line:"#35291a","line-soft":"#281f14",fg:"#f5e8d2","fg-2":"#c4ac8a",dim:"#8a7355",accent:"#ffb020","accent-deep":"#d2690c","accent-wash":"#33220a",magenta:"#ff5f3a","magenta-wash":"#331309",ok:"#9ecb3a",warn:"#ffd54a",crit:"#ff4a3d",track:"#241c11","on-accent":"#1a1000"},light:{bg:"#f5f0e6",surface:"#fffdf8","surface-2":"#faf5ea",inset:"#efe7d6",line:"#d9cdb4","line-soft":"#e8dfcc",fg:"#201705","fg-2":"#5b4a2d",dim:"#7d6a48",accent:"#a35c00","accent-deep":"#7c3d05","accent-wash":"#f6e6c8",magenta:"#b53a17","magenta-wash":"#fadfd6",ok:"#4d6b12",warn:"#8a5804",crit:"#b02a20",track:"#e3d8c2","on-accent":"#fffdf8"}},{id:"verdant",name:"Verdant",dark:{bg:"#040b07",surface:"#0a150f","surface-2":"#0f1d16",inset:"#0c1811",line:"#1c3226","line-soft":"#152920",fg:"#ddf5e5","fg-2":"#9cc0ab",dim:"#5d8570",accent:"#7ee787","accent-deep":"#26a269","accent-wash":"#0f2b1c",magenta:"#3ddbd9","magenta-wash":"#0a2a2c",ok:"#7ee787",warn:"#ffc94a",crit:"#ff5f6d",track:"#12281c","on-accent":"#04140a"},light:{bg:"#eef4ef",surface:"#ffffff","surface-2":"#f5faf6",inset:"#e6efe8",line:"#c7d9cc","line-soft":"#dbe8de",fg:"#0a1a10","fg-2":"#385643",dim:"#5a7864",accent:"#1a7f4b","accent-deep":"#115e37","accent-wash":"#d7f0e0",magenta:"#0d7d7b","magenta-wash":"#d4f0ef",ok:"#1a7f4b",warn:"#8a5804",crit:"#b52436",track:"#d9e5db","on-accent":"#ffffff"}},{id:"plasma",name:"Plasma",dark:{bg:"#07050f",surface:"#110d1e","surface-2":"#191330",inset:"#140f26",line:"#2c2350","line-soft":"#211a3e",fg:"#eae4ff","fg-2":"#b3a8d8",dim:"#7568a8",accent:"#a06bff","accent-deep":"#5b3ed6","accent-wash":"#22164a",magenta:"#ff5bc8","magenta-wash":"#2e0f2a",ok:"#4ddba0",warn:"#ffc046",crit:"#ff5470",track:"#1c1638","on-accent":"#0b0618"},light:{bg:"#f1eef8",surface:"#ffffff","surface-2":"#f8f5fd",inset:"#ebe6f6",line:"#d2c8e8","line-soft":"#e2dbf1",fg:"#150c28","fg-2":"#47395f",dim:"#6b5c88",accent:"#6b2fd0","accent-deep":"#4a1aa8","accent-wash":"#e7dbfb",magenta:"#b81f86","magenta-wash":"#fbdcf0",ok:"#0f7a52",warn:"#8a5804",crit:"#b52440",track:"#e0d8f0","on-accent":"#ffffff"}},{id:"ember",name:"Ember",dark:{bg:"#0a0605",surface:"#150e0b","surface-2":"#1e1511",inset:"#191110",line:"#38231b","line-soft":"#2a1a15",fg:"#f7e6dd","fg-2":"#c7a696",dim:"#8d6a5c",accent:"#ff6b3d","accent-deep":"#c22f1e","accent-wash":"#331408",magenta:"#ffc247","magenta-wash":"#2e2209",ok:"#58c98a",warn:"#ffc247",crit:"#ff3b30",track:"#251712","on-accent":"#190802"},light:{bg:"#f6f0ec",surface:"#ffffff","surface-2":"#fbf5f1",inset:"#efe4dd",line:"#ddc9bd","line-soft":"#ebdcd3",fg:"#22110a","fg-2":"#5e4235",dim:"#7f6153",accent:"#c1401b","accent-deep":"#922b12","accent-wash":"#fadfd3",magenta:"#8a6206","magenta-wash":"#f7e9c9",ok:"#0f7a44",warn:"#8a5804",crit:"#b52436",track:"#e6d6cb","on-accent":"#ffffff"}},{id:"glacier",name:"Glacier",dark:{bg:"#060a10",surface:"#0d141d","surface-2":"#131d29",inset:"#101825",line:"#223549","line-soft":"#1a2b3c",fg:"#e4eef8","fg-2":"#a6bccf",dim:"#67839c",accent:"#63b3ff","accent-deep":"#2f6fd0","accent-wash":"#112a45",magenta:"#9fd8e8","magenta-wash":"#10262e",ok:"#4fd1a5",warn:"#ffcb5c",crit:"#ff6b7d",track:"#16232f","on-accent":"#04101d"},light:{bg:"#eef2f7",surface:"#ffffff","surface-2":"#f6f9fc",inset:"#e7edf4",line:"#c8d5e3","line-soft":"#dde5ee",fg:"#0b1622","fg-2":"#3c5064",dim:"#5f7488",accent:"#1462b8","accent-deep":"#0c4383","accent-wash":"#d9e9fb",magenta:"#2a7f96","magenta-wash":"#d6eef4",ok:"#0f7a52",warn:"#8a5804",crit:"#b52440",track:"#dbe4ee","on-accent":"#ffffff"}},{id:"ha",name:"Home Assistant",dark:{bg:"var(--primary-background-color, #05090f)",surface:"var(--card-background-color, #0b131d)","surface-2":"var(--secondary-background-color, #101b28)",inset:"var(--secondary-background-color, #0d1723)",line:"var(--divider-color, #1b2b3d)","line-soft":"var(--divider-color, #152435)",fg:"var(--primary-text-color, #dff2f6)","fg-2":"var(--secondary-text-color, #9fb8c6)",dim:"var(--secondary-text-color, #5d7d92)",accent:"var(--primary-color, #2ae6dc)","accent-deep":"var(--dark-primary-color, #1b8fd6)","accent-wash":"var(--secondary-background-color, #0e2b30)",magenta:"var(--accent-color, #ff3ea5)","magenta-wash":"var(--secondary-background-color, #2a0d1e)",ok:"var(--success-color, #35d67a)",warn:"var(--warning-color, #ffb020)",crit:"var(--error-color, #ff4d5e)",track:"var(--divider-color, #132434)","on-accent":"var(--text-primary-color, #04141a)"}}],Ye="reactor";function be(s){return de.find(e=>e.id===s)??de[0]}function at(s){return!be(s).light}function it(s,e,t){const r=be(e),o=t&&r.light||r.dark,n=r.id===Ye;for(const[a,c]of Object.entries(o)){const i=`--gp-${a}`;n?s.style.removeProperty(i):s.style.setProperty(i,c)}}const ct=B`
  :host {
    --gp-bg: #05090f;
    --gp-surface: #0b131d;
    --gp-surface-2: #101b28;
    --gp-inset: #0d1723;
    --gp-line: #1b2b3d;
    --gp-line-soft: #152435;
    --gp-fg: #dff2f6;
    --gp-fg-2: #9fb8c6;
    --gp-dim: #5d7d92;
    --gp-accent: #2ae6dc;
    --gp-accent-deep: #1b8fd6;
    --gp-accent-wash: #0e2b30;
    --gp-magenta: #ff3ea5;
    --gp-magenta-wash: #2a0d1e;
    --gp-ok: #35d67a;
    --gp-warn: #ffb020;
    --gp-crit: #ff4d5e;
    --gp-track: #132434;
    --gp-on-accent: #04141a;
  }
  :host([light]) {
    --gp-bg: #eef2f6;
    --gp-surface: #ffffff;
    --gp-surface-2: #f6f9fb;
    --gp-inset: #e8eef3;
    --gp-line: #cbd8e2;
    --gp-line-soft: #dfe7ee;
    --gp-fg: #0c1a24;
    --gp-fg-2: #3a5162;
    --gp-dim: #5b7484;
    --gp-accent: #0c847e;
    --gp-accent-deep: #0f5f8c;
    --gp-accent-wash: #d9f0ee;
    --gp-magenta: #b4176e;
    --gp-magenta-wash: #fbe4f0;
    --gp-ok: #0f7a44;
    --gp-warn: #8a5804;
    --gp-crit: #b52436;
    --gp-track: #dae3ea;
    --gp-on-accent: #ffffff;
  }
`,dt=B`
  :host {
    --gp-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    --gp-sans: var(--paper-font-body1_-_font-family, "Roboto", system-ui, -apple-system, sans-serif);
    display: block;
    color: var(--gp-fg);
    font-family: var(--gp-sans);
    font-size: 15px;
    line-height: 1.5;
  }
  * {
    box-sizing: border-box;
  }
  .card {
    background: var(--gp-surface);
    border: 1px solid var(--gp-line);
    border-radius: 10px;
    padding: 16px 18px;
  }
  .label {
    font-family: var(--gp-mono);
    font-size: 10px;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: var(--gp-dim);
  }
  .value {
    font-family: var(--gp-mono);
    font-variant-numeric: tabular-nums;
    font-weight: 600;
  }
  .grid {
    display: grid;
    gap: 12px;
  }
  .grid > * {
    min-width: 0;
  }
  h2 {
    margin: 0 0 12px;
    font-size: 15px;
    font-weight: 600;
    letter-spacing: 0.02em;
  }
  button {
    font: inherit;
    color: inherit;
  }
  .btn {
    background: var(--gp-surface-2);
    border: 1px solid var(--gp-line);
    border-radius: 8px;
    padding: 7px 14px;
    cursor: pointer;
  }
  .btn:hover:not(:disabled) {
    border-color: var(--gp-accent);
  }
  .btn.primary {
    background: var(--gp-accent);
    border-color: var(--gp-accent);
    color: var(--gp-on-accent);
  }
  .btn.danger {
    border-color: var(--gp-crit);
    color: var(--gp-crit);
  }
  .btn:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
  select,
  input[type="number"] {
    font: inherit;
    color: var(--gp-fg);
    background: var(--gp-inset);
    border: 1px solid var(--gp-line);
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 0;
  }
  select:disabled,
  input:disabled {
    opacity: 0.5;
  }
  .row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    padding: 9px 0;
    border-top: 1px solid var(--gp-line-soft);
  }
  .row:first-of-type {
    border-top: none;
  }
  .pill {
    font-family: var(--gp-mono);
    font-size: 10.5px;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 2px 8px;
    border-radius: 999px;
    border: 1px solid var(--gp-line);
    color: var(--gp-dim);
  }
  .pill.ok {
    color: var(--gp-ok);
    border-color: var(--gp-ok);
  }
  .pill.bad {
    color: var(--gp-crit);
    border-color: var(--gp-crit);
  }
  .note {
    color: var(--gp-dim);
    font-size: 13px;
  }
`;export{h as A,Ye as D,de as S,x as a,dt as b,nt as c,it as d,L as e,at as f,ge as g,tt as h,B as i,st as j,be as k,ot as l,g as n,et as r,rt as s,ct as t,Ve as w};
