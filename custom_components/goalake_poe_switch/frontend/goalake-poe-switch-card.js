import{t as $,b as g,i as f,n as u,r,a as v,c as b,l as m,f as w,d as x,e as l,A as k,w as C,S as P,g as y}from"./goalake-poe-switch-shared.js";var S=Object.defineProperty,E=Object.getOwnPropertyDescriptor,o=(t,s,i,e)=>{for(var a=e>1?void 0:e?E(s,i):s,h=t.length-1,p;h>=0;h--)(p=t[h])&&(a=(e?p(s,i,a):p(a))||a);return e&&a&&S(s,i,a),a};const _="goalake_poe_switch",n="goalake-poe-switch-card";let c=class extends v{constructor(){super(...arguments),this._config={type:`custom:${n}`},this._devices=[],this._catalogue={},this._error="",this._confirm=null,this._subscribing=!1,this._t=(t,s)=>b(this._catalogue,t,s)}static getConfigElement(){return document.createElement(`${n}-editor`)}static getStubConfig(){return{interactive:!1}}setConfig(t){this._config={...t}}getCardSize(){return 3}connectedCallback(){super.connectedCallback(),this.hass&&this._subscribe()}disconnectedCallback(){super.disconnectedCallback(),this._unsub?.(),this._unsub=void 0}willUpdate(t){t.has("hass")&&this.hass&&(this._subscribe(),m(this.hass.language).then(s=>this._catalogue=s))}updated(){const t=this._config.scheme??"ha",s=this.hass?.themes?.darkMode===!1;this.toggleAttribute("light",!w(t)&&s),x(this,t,s)}async _subscribe(){if(!(this._unsub||this._subscribing||!this.isConnected)){this._subscribing=!0;try{this._unsub=await this.hass.connection.subscribeMessage(t=>this._devices=t.devices,{type:`${_}/subscribe`})}catch{this._error="–"}finally{this._subscribing=!1}}}get _device(){const t=this._config.entry_id;return t?this._devices.find(s=>s.entry_id===t):this._devices[0]}async _setPoe(t,s){const i=this._device;if(i)try{this._error="",await this.hass.callWS({type:`${_}/write`,entry_id:i.entry_id,action:"poe",index:t,value:s})}catch(e){this._error=e&&typeof e=="object"&&"message"in e?String(e.message):String(e)}}_portClicked(t,s){const i=s.ports.find(e=>e.index===t);!i||!i.is_poe||!this._config.interactive||!this.hass.user?.is_admin||(i.poe_enabled?this._confirm={index:t,label:i.label}:this._setPoe(t,!0))}render(){const t=this._device;if(!t)return l`<ha-card><span class="note">${this._t(this._devices.length?"card.pick":"card.no_device")}</span></ha-card>`;const s=this._config.ports?.length?t.ports.filter(e=>this._config.ports.includes(e.label)):t.ports,i=!!(this._config.interactive&&this.hass?.user?.is_admin);return l`<ha-card>
      <div class="head">
        <span class="title">${this._config.title||t.title}</span>
        <span class="pill ${t.available?"ok":"bad"}">${this._t(t.available?"state.online":"state.offline")}</span>
      </div>
      <div class="stats">
        <div><div class="label">${this._t("stat.power")}</div><div class="value">${C(t.total_power_w)}</div></div>
        <div><div class="label">${this._t("stat.temperature")}</div><div class="value">${t.temperature_c===null?"–":`${t.temperature_c.toFixed(1)} °C`}</div></div>
      </div>
      <gp-port-grid .ports=${s} ?readonly=${!i} @port-select=${e=>this._portClicked(e.detail,t)}></gp-port-grid>
      ${this._error?l`<div class="error" role="alert">${this._error}</div>`:k}
      <gp-confirm
        ?open=${this._confirm!==null}
        .heading=${this._t("confirm.title")}
        .message=${this._confirm?this._t("confirm.poe_off",{port:this._confirm.label}):""}
        .okLabel=${this._t("confirm.ok")}
        .cancelLabel=${this._t("confirm.cancel")}
        @cancel=${()=>this._confirm=null}
        @confirm=${()=>{const e=this._confirm;this._confirm=null,e&&this._setPoe(e.index,!1)}}
      ></gp-confirm>
    </ha-card>`}};c.styles=[$,g,f`
      ha-card {
        padding: 14px 16px;
        background: var(--gp-surface);
        color: var(--gp-fg);
      }
      .head {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        margin-bottom: 8px;
      }
      .title {
        font-weight: 600;
        font-size: 16px;
      }
      .stats {
        display: flex;
        gap: 24px;
        margin-bottom: 12px;
      }
      .error {
        color: var(--gp-crit);
        font-size: 13px;
        margin-top: 8px;
      }
    `];o([u({attribute:!1})],c.prototype,"hass",2);o([r()],c.prototype,"_config",2);o([r()],c.prototype,"_devices",2);o([r()],c.prototype,"_catalogue",2);o([r()],c.prototype,"_error",2);o([r()],c.prototype,"_confirm",2);c=o([y(n)],c);let d=class extends v{constructor(){super(...arguments),this._config={type:`custom:${n}`},this._devices=[],this._catalogue={},this._loaded=!1,this._t=t=>b(this._catalogue,t)}setConfig(t){this._config={...t}}willUpdate(t){t.has("hass")&&this.hass&&!this._loaded&&(this._loaded=!0,this.hass.callWS({type:`${_}/devices`}).then(s=>this._devices=s).catch(()=>{}),m(this.hass.language).then(s=>this._catalogue=s))}_change(t){const s={...this._config,...t};for(const i of Object.keys(s)){const e=s[i];(e===void 0||e===""||Array.isArray(e)&&e.length===0)&&delete s[i]}this._config=s,this.dispatchEvent(new CustomEvent("config-changed",{detail:{config:s},bubbles:!0,composed:!0}))}get _device(){const t=this._config.entry_id;return t?this._devices.find(s=>s.entry_id===t):this._devices[0]}render(){const t=this._device,s=t?[...t.ports].sort((e,a)=>Number(a.is_poe)-Number(e.is_poe)||(e.is_poe?Number(e.label)-Number(a.label):e.label.localeCompare(a.label))).map(e=>e.label):[],i=this._config.ports?.length?this._config.ports:s;return l`
      <div class="field">
        <span class="label">${this._t("card.device")}</span>
        <select @change=${e=>this._change({entry_id:e.target.value,ports:void 0})}>
          ${this._devices.map(e=>l`<option value=${e.entry_id} ?selected=${e.entry_id===t?.entry_id}>${e.title}</option>`)}
        </select>
      </div>
      <div class="field">
        <span class="label">${this._t("card.title")}</span>
        <input type="text" .value=${this._config.title??""} @input=${e=>this._change({title:e.target.value})} />
      </div>
      <div class="field">
        <span class="label">${this._t("card.ports")}</span>
        <div class="ports">
          ${s.map(e=>l`<label class="check"><input type="checkbox" .checked=${i.includes(e)} @change=${a=>this._togglePort(e,a.target.checked,s,i)} />${e}</label>`)}
        </div>
      </div>
      <div class="field">
        <label class="check"><input type="checkbox" .checked=${!!this._config.interactive} @change=${e=>this._change({interactive:e.target.checked||void 0})} />${this._t("card.interactive")}</label>
      </div>
      <div class="field">
        <span class="label">${this._t("card.scheme")}</span>
        <select @change=${e=>this._change({scheme:e.target.value==="ha"?void 0:e.target.value})}>
          ${[...P].sort((e,a)=>e.id==="ha"?-1:a.id==="ha"?1:0).map(e=>l`<option value=${e.id} ?selected=${(this._config.scheme??"ha")===e.id}>${e.name}</option>`)}
        </select>
      </div>
    `}_togglePort(t,s,i,e){const a=s?[...new Set([...e,t])]:e.filter(h=>h!==t);this._change({ports:a.length===i.length?void 0:a})}};d.styles=[g,f`
      :host {
        display: block;
      }
      .field {
        display: flex;
        flex-direction: column;
        gap: 4px;
        margin-bottom: 14px;
      }
      .ports {
        display: flex;
        flex-wrap: wrap;
        gap: 6px 14px;
      }
      label.check {
        display: flex;
        align-items: center;
        gap: 6px;
        color: var(--primary-text-color);
      }
      select,
      input[type="text"] {
        font: inherit;
        padding: 8px 10px;
        border-radius: 6px;
        border: 1px solid var(--divider-color, #888);
        background: var(--card-background-color, #fff);
        color: var(--primary-text-color);
      }
      .label {
        color: var(--secondary-text-color);
      }
    `];o([u({attribute:!1})],d.prototype,"hass",2);o([r()],d.prototype,"_config",2);o([r()],d.prototype,"_devices",2);o([r()],d.prototype,"_catalogue",2);d=o([y(`${n}-editor`)],d);window.customCards=window.customCards??[];window.customCards.some(t=>t.type===n)||window.customCards.push({type:n,name:"PoE Switch",description:"Ports, power and PoE control of a Goalake / Amitres PoE switch",preview:!1});
