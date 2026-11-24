import{i as $,n as d,a as P,e as r,g as b,b as k,r as c,A as l,w as x,s as j,h as O,S as I,j as T,k as U,t as A,D as L,c as B,f as F,d as G,l as R}from"./goalake-poe-switch-shared.js";var M=Object.defineProperty,N=Object.getOwnPropertyDescriptor,D=(t,e,s,a)=>{for(var i=a>1?void 0:a?N(e,s):e,o=t.length-1,n;o>=0;o--)(n=t[o])&&(i=(a?n(e,s,i):n(i))||i);return a&&i&&M(e,s,i),i};let m=class extends P{constructor(){super(...arguments),this.checked=!1,this.disabled=!1}render(){return r`<button
      role="switch"
      aria-checked=${this.checked?"true":"false"}
      ?disabled=${this.disabled}
      @click=${()=>this.dispatchEvent(new CustomEvent("toggle",{detail:!this.checked}))}
    >
      <span></span>
    </button>`}};m.styles=$`
    button {
      width: 42px;
      height: 24px;
      border-radius: 999px;
      border: 1px solid var(--gp-line, #1b2b3d);
      background: var(--gp-track, #132434);
      position: relative;
      cursor: pointer;
      padding: 0;
      transition: background 0.15s;
    }
    button[aria-checked="true"] {
      background: var(--gp-accent, #2ae6dc);
      border-color: var(--gp-accent, #2ae6dc);
    }
    button:disabled {
      opacity: 0.45;
      cursor: not-allowed;
    }
    span {
      position: absolute;
      top: 2px;
      left: 2px;
      width: 18px;
      height: 18px;
      border-radius: 50%;
      background: var(--gp-fg, #dff2f6);
      transition: transform 0.15s;
    }
    button[aria-checked="true"] span {
      transform: translateX(18px);
      background: var(--gp-on-accent, #04141a);
    }
  `;D([d({type:Boolean})],m.prototype,"checked",2);D([d({type:Boolean})],m.prototype,"disabled",2);m=D([b("gp-toggle")],m);var z=Object.defineProperty,S=(t,e,s,a)=>{for(var i=void 0,o=t.length-1,n;o>=0;o--)(n=t[o])&&(i=n(e,s,i)||i);return i&&z(e,s,i),i};class f extends P{constructor(){super(...arguments),this.t=e=>e,this.admin=!1}fire(e,s){this.dispatchEvent(new CustomEvent(e,{detail:s,bubbles:!0,composed:!0}))}write(e,s){this.fire("write",{entry_id:e,request:s})}}S([d({attribute:!1})],f.prototype,"t");S([d({type:Boolean})],f.prototype,"admin");var W=Object.defineProperty,q=Object.getOwnPropertyDescriptor,u=(t,e,s,a)=>{for(var i=a>1?void 0:a?q(e,s):e,o=t.length-1,n;o>=0;o--)(n=t[o])&&(i=(a?n(e,s,i):n(i))||i);return a&&i&&W(e,s,i),i};const H=["down","10m_half","10m_full","100m_half","100m_full","1000m_full"];let h=class extends f{constructor(){super(...arguments),this.devices=[],this.selectedId="",this._port=null,this._pending=null,this._limitUp="",this._limitDown="",this._limitPort=null}get _device(){return this.devices.find(t=>t.entry_id===this.selectedId)??this.devices[0]}render(){const t=this._device;if(!t)return r`<div class="card note">${this.t("overview.empty")}</div>`;const e=this._port===null?void 0:t.ports.find(s=>s.index===this._port);return r`
      ${this.devices.length>1?r`<div class="tabs">
            ${this.devices.map(s=>r`<button class="tab ${s.entry_id===t.entry_id?"active":""}" @click=${()=>this._choose(s.entry_id)}>${s.title}</button>`)}
          </div>`:l}
      <div class="grid stats">
        ${this._stat("stat.power",x(t.total_power_w))}
        ${this._stat("stat.voltage",t.voltage_v===null?"–":`${t.voltage_v} V`)}
        ${this._stat("stat.temperature",t.temperature_c===null?"–":`${t.temperature_c.toFixed(1)} °C`)}
        ${this._stat("stat.firmware",t.firmware)}
        ${this._stat("stat.cloud",t.cloud_status===null?"–":this.t(t.cloud_status?"stat.cloud_on":"stat.cloud_off"))}
      </div>
      <div class="card">
        <gp-port-grid .ports=${t.ports} .selected=${this._port} @port-select=${s=>this._port=s.detail}></gp-port-grid>
      </div>
      <div class="card detail">${e?this._portDetail(t,e):r`<span class="note">${this.t("port.hint")}</span>`}</div>
      <gp-confirm
        ?open=${this._pending!==null}
        .heading=${this.t("confirm.title")}
        .message=${this._pending?.message??""}
        .okLabel=${this.t("confirm.ok")}
        .cancelLabel=${this.t("confirm.cancel")}
        @cancel=${()=>this._pending=null}
        @confirm=${()=>{const s=this._pending?.run;this._pending=null,s?.()}}
      ></gp-confirm>
    `}_stat(t,e){return r`<div class="card stat"><div class="label">${this.t(t)}</div><div class="value">${e}</div></div>`}_choose(t){this._port=null,this.fire("select-device",t)}_portDetail(t,e){const s=i=>this.write(t.entry_id,{...i,index:e.index}),a=this.admin&&e.is_poe;return this._limitPort!==e.index&&(this._limitPort=e.index,this._limitUp=String(e.limit_up_mbps??0),this._limitDown=String(e.limit_down_mbps??0)),r`
      <h2>${this.t("port.title",{port:e.label})}</h2>
      <div class="metrics">
        <div><div class="label">${this.t("port.link")}</div><div class="value">${e.connected?j(e.speed_mbps):this.t("port.no_link")}</div></div>
        ${e.is_poe?r`<div><div class="label">${this.t("port.power")}</div><div class="value">${x(e.power_w)}</div></div>`:l}
        <div><div class="label">${this.t("port.tx")}</div><div class="value">${O(e.tx_kbps)}</div></div>
        <div><div class="label">${this.t("port.rx")}</div><div class="value">${O(e.rx_kbps)}</div></div>
      </div>
      ${e.is_poe?l:r`<p class="note">${this.t("port.uplink_note")}</p>`}
      ${e.is_poe&&!this.admin?r`<p class="note">${this.t("admin.required")}</p>`:l}
      ${e.is_poe?r`
            <div class="row">
              <span>${this.t("port.poe")}</span>
              <gp-toggle
                .checked=${e.poe_enabled===!0}
                ?disabled=${!a}
                @toggle=${i=>i.detail?s({action:"poe",value:!0}):this._ask(this.t("confirm.poe_off",{port:e.label}),()=>s({action:"poe",value:!1}))}
              ></gp-toggle>
            </div>
            <div class="row">
              <span>${this.t("port.extend")}</span>
              <gp-toggle
                .checked=${e.phy_mode==="10m_half"||e.phy_mode==="10m_full"}
                ?disabled=${!a}
                @toggle=${i=>s({action:"extend",value:i.detail})}
              ></gp-toggle>
            </div>
            <div class="row">
              <span>${this.t("port.mode")}</span>
              <select ?disabled=${!a} .value=${e.phy_mode??""} @change=${i=>s({action:"mode",value:i.target.value})}>
                ${H.map(i=>r`<option value=${i} ?selected=${e.phy_mode===i}>${this.t(`mode.${i}`)}</option>`)}
              </select>
            </div>
            <div class="row">
              <span>${this.t("port.priority")}</span>
              <select ?disabled=${!a} @change=${i=>s({action:"priority",value:Number(i.target.value)})}>
                ${[0,1,2,3,4,5,6].map(i=>r`<option value=${i} ?selected=${e.priority===i}>${i}</option>`)}
              </select>
            </div>
            <div class="row">
              <span>${this.t("port.limit_up")}</span>
              <span class="limit">
                <input type="number" min="0" max="1000" .value=${this._limitUp} ?disabled=${!a} @input=${i=>this._limitUp=i.target.value} />
                <button class="btn" ?disabled=${!a} @click=${()=>s({action:"limit_up",value:Number(this._limitUp)})}>${this.t("port.apply")}</button>
              </span>
            </div>
            <div class="row">
              <span>${this.t("port.limit_down")}</span>
              <span class="limit">
                <input type="number" min="0" max="1000" .value=${this._limitDown} ?disabled=${!a} @input=${i=>this._limitDown=i.target.value} />
                <button class="btn" ?disabled=${!a} @click=${()=>s({action:"limit_down",value:Number(this._limitDown)})}>${this.t("port.apply")}</button>
              </span>
            </div>
            <div class="row">
              <span>${this.t("port.flow")}</span>
              <gp-toggle .checked=${e.flow_control===!0} ?disabled=${!a} @toggle=${i=>s({action:"flow",value:i.detail})}></gp-toggle>
            </div>
            <div class="row">
              <span></span>
              <button class="btn danger" ?disabled=${!a} @click=${()=>this._ask(this.t("confirm.restart_port",{port:e.label}),()=>s({action:"restart_port"}))}>${this.t("port.restart")}</button>
            </div>
          `:l}
    `}_ask(t,e){this._pending={message:t,run:e}}};h.styles=[k,$`
      .tabs {
        display: flex;
        gap: 8px;
        margin-bottom: 12px;
        flex-wrap: wrap;
      }
      .tab {
        padding: 5px 12px;
        border-radius: 999px;
        border: 1px solid var(--gp-line);
        background: var(--gp-surface);
        cursor: pointer;
      }
      .tab.active {
        border-color: var(--gp-accent);
        color: var(--gp-accent);
      }
      .stats {
        grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
        margin-bottom: 12px;
      }
      .stat .value {
        font-size: 20px;
      }
      .detail {
        margin-top: 12px;
      }
      .metrics {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
        gap: 10px;
        margin-bottom: 8px;
      }
      .limit {
        display: flex;
        gap: 8px;
        align-items: center;
      }
      .limit input {
        width: 90px;
      }
    `];u([d({attribute:!1})],h.prototype,"devices",2);u([d()],h.prototype,"selectedId",2);u([c()],h.prototype,"_port",2);u([c()],h.prototype,"_pending",2);u([c()],h.prototype,"_limitUp",2);u([c()],h.prototype,"_limitDown",2);h=u([b("gp-device")],h);var V=Object.defineProperty,X=Object.getOwnPropertyDescriptor,C=(t,e,s,a)=>{for(var i=a>1?void 0:a?X(e,s):e,o=t.length-1,n;o>=0;o--)(n=t[o])&&(i=(a?n(e,s,i):n(i))||i);return a&&i&&V(e,s,i),i};let y=class extends f{constructor(){super(...arguments),this.devices=[]}render(){if(!this.devices.length)return r`<div class="card note">${this.t("overview.empty")}</div>`;const t=this.devices.reduce((e,s)=>e+(s.total_power_w??0),0);return r`
      <div class="summary">
        <div>
          <div class="label">${this.t("overview.total_power")}</div>
          <div class="value big">${x(t)}</div>
        </div>
        <div>
          <div class="label">${this.t("overview.switches")}</div>
          <div class="value big">${this.devices.length}</div>
        </div>
      </div>
      <div class="grid cards">${this.devices.map(e=>this._card(e))}</div>
    `}_card(t){const e=t.ports.filter(s=>s.connected).length;return r`<div class="card" @click=${()=>this.fire("open-device",t.entry_id)}>
      <div class="head">
        <div>
          <div class="title">${t.title}</div>
          <div class="note">${t.model??""} ${t.firmware}</div>
        </div>
        <span class="pill ${t.available?"ok":"bad"}">${this.t(t.available?"state.online":"state.offline")}</span>
      </div>
      <div class="metrics">
        <div>
          <div class="label">${this.t("stat.power")}</div>
          <div class="value">${x(t.total_power_w)}</div>
        </div>
        <div>
          <div class="label">${this.t("stat.temperature")}</div>
          <div class="value">${t.temperature_c===null?"–":`${t.temperature_c.toFixed(1)} °C`}</div>
        </div>
      </div>
      <gp-port-grid compact .ports=${t.ports}></gp-port-grid>
      <div class="note" style="margin-top:8px">${this.t("overview.ports_linked",{n:e,m:t.ports.length})}</div>
    </div>`}};y.styles=[k,$`
      .summary {
        display: flex;
        gap: 28px;
        flex-wrap: wrap;
        margin-bottom: 14px;
      }
      .big {
        font-size: 26px;
      }
      .cards {
        grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      }
      .card {
        cursor: pointer;
      }
      .card:hover {
        border-color: var(--gp-accent);
      }
      .head {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 8px;
        margin-bottom: 10px;
      }
      .title {
        font-weight: 600;
      }
      .metrics {
        display: flex;
        gap: 22px;
        margin: 10px 0;
      }
    `];C([d({attribute:!1})],y.prototype,"devices",2);y=C([b("gp-overview")],y);var J=Object.defineProperty,K=Object.getOwnPropertyDescriptor,_=(t,e,s,a)=>{for(var i=a>1?void 0:a?K(e,s):e,o=t.length-1,n;o>=0;o--)(n=t[o])&&(i=(a?n(e,s,i):n(i))||i);return a&&i&&J(e,s,i),i};const Q=[["lldp","feature.lldp","lldp"],["storm","feature.storm","storm"],["watchdog","feature.watchdog","watchdog"],["ai_auto_extend","feature.ai_auto_extend","ai_auto_extend"]];let v=class extends f{constructor(){super(...arguments),this.devices=[],this.selectedId="",this._confirmReboot=!1,this._warn="",this._warnFor=""}get _device(){return this.devices.find(t=>t.entry_id===this.selectedId)??this.devices[0]}render(){const t=this._device;return r`<div class="grid sections">
      <div class="card">
        <h2>${this.t("settings.appearance")}</h2>
        <div class="label" style="margin-bottom:6px">${this.t("settings.palette")}</div>
        <div class="schemes">${I.map(e=>this._scheme(e.id,e.name))}</div>
        <div class="row">
          <span>${this.t("settings.mode")}</span>
          <span class="segment">
            ${["auto","dark","light"].map(e=>r`<button class="btn ${this.settings.mode===e?"primary":""}" @click=${()=>this.fire("settings-change",{mode:e})}>${this.t(`settings.mode.${e}`)}</button>`)}
          </span>
        </div>
        <div class="row">
          <span>${this.t("settings.language")}</span>
          <select @change=${e=>this.fire("settings-change",{language:e.target.value})}>
            <option value="auto" ?selected=${this.settings.language==="auto"}>${this.t("settings.language.auto")}</option>
            ${T.map(e=>r`<option value=${e} ?selected=${this.settings.language===e}>${e.toUpperCase()}</option>`)}
          </select>
        </div>
      </div>
      ${t?this._features(t):l}
    </div>`}_scheme(t,e){const s=U(t),a=t==="ha"?["#3b82f6","#ffffff","#9ca3af"]:[s.dark.bg,s.dark.accent,s.dark.magenta,s.dark.ok];return r`<button class="scheme ${this.settings.scheme===t?"active":""}" @click=${()=>this.fire("settings-change",{scheme:t})}>
      <div class="swatch">${a.map(i=>r`<span style="background:${i}"></span>`)}</div>
      <span>${e}</span>
    </button>`}_features(t){const e=(s,a)=>this.write(t.entry_id,{action:s,value:a});return this._warnFor!==t.entry_id&&(this._warnFor=t.entry_id,this._warn=String(t.settings.power_warn??0)),r`<div class="card">
        <h2>${this.t("settings.features")} · ${t.title}</h2>
        ${this.admin?l:r`<p class="note">${this.t("admin.required")}</p>`}
        ${Q.map(([s,a,i])=>r`<div class="row">
            <span>${this.t(a)}</span>
            <gp-toggle .checked=${!!t.settings[s]} ?disabled=${!this.admin} @toggle=${o=>e(i,o.detail)}></gp-toggle>
          </div>`)}
        <div class="row">
          <span>${this.t("feature.power_warn")}</span>
          <span style="display:flex;gap:8px">
            <input type="number" min="0" max="1000" .value=${this._warn} ?disabled=${!this.admin} @input=${s=>this._warn=s.target.value} />
            <button class="btn" ?disabled=${!this.admin} @click=${()=>e("power_warn",Number(this._warn))}>${this.t("port.apply")}</button>
          </span>
        </div>
      </div>
      <div class="card warn">
        <h2>${this.t("settings.maintenance")}</h2>
        <div class="row">
          <span></span>
          <button class="btn danger" ?disabled=${!this.admin} @click=${()=>this._confirmReboot=!0}>${this.t("settings.reboot")}</button>
        </div>
      </div>
      <gp-confirm
        ?open=${this._confirmReboot}
        .heading=${this.t("confirm.title")}
        .message=${this.t("confirm.reboot")}
        .okLabel=${this.t("confirm.ok")}
        .cancelLabel=${this.t("confirm.cancel")}
        @cancel=${()=>this._confirmReboot=!1}
        @confirm=${()=>{this._confirmReboot=!1,this.write(t.entry_id,{action:"reboot",confirm:!0})}}
      ></gp-confirm>`}};v.styles=[k,$`
      .sections {
        grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
        align-items: start;
      }
      .schemes {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
        gap: 8px;
        margin-bottom: 12px;
      }
      .scheme {
        border: 1px solid var(--gp-line);
        background: var(--gp-surface-2);
        border-radius: 8px;
        padding: 8px;
        cursor: pointer;
        text-align: left;
      }
      .scheme.active {
        border-color: var(--gp-accent);
        box-shadow: 0 0 0 1px var(--gp-accent);
      }
      .swatch {
        display: flex;
        height: 14px;
        border-radius: 4px;
        overflow: hidden;
        margin-bottom: 6px;
      }
      .swatch span {
        flex: 1;
      }
      .segment {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;
      }
      .warn {
        border-color: var(--gp-warn);
      }
      input[type="number"] {
        width: 90px;
      }
    `];_([d({attribute:!1})],v.prototype,"settings",2);_([d({attribute:!1})],v.prototype,"devices",2);_([d()],v.prototype,"selectedId",2);_([c()],v.prototype,"_confirmReboot",2);_([c()],v.prototype,"_warn",2);v=_([b("gp-settings")],v);var Y=Object.defineProperty,Z=Object.getOwnPropertyDescriptor,g=(t,e,s,a)=>{for(var i=a>1?void 0:a?Z(e,s):e,o=t.length-1,n;o>=0;o--)(n=t[o])&&(i=(a?n(e,s,i):n(i))||i);return a&&i&&Y(e,s,i),i};const w="goalake_poe_switch",E={scheme:L,mode:"auto",language:"auto",device:""};let p=class extends P{constructor(){super(...arguments),this.narrow=!1,this._devices=[],this._view="overview",this._settings={...E},this._catalogue={},this._error="",this._started=!1,this._t=(t,e)=>B(this._catalogue,t,e)}willUpdate(t){t.has("hass")&&this.hass&&!this._started&&(this._started=!0,this._start()),(t.has("hass")||t.has("_settings"))&&this._loadLanguage()}updated(){const t=this._settings,e=t.mode==="light"||t.mode==="auto"&&this.hass?.themes?.darkMode===!1;this.toggleAttribute("light",!F(t.scheme)&&e),G(this,t.scheme,e)}disconnectedCallback(){super.disconnectedCallback(),this._unsub?.(),this._unsub=void 0,this._started=!1}async _start(){try{const t=await this.hass.callWS({type:`${w}/settings/get`});this._settings={...E,...t},this._unsub=await this.hass.connection.subscribeMessage(e=>{this._devices=e.devices},{type:`${w}/subscribe`})}catch(t){this._showError(this._t("error.load",{message:this._message(t)}))}}async _loadLanguage(){const t=this._settings.language==="auto"?this.hass?.language??"en":this._settings.language;this._catalogue=await R(t)}_message(t){return t&&typeof t=="object"&&"message"in t?String(t.message):String(t)}_showError(t){this._error=t,window.clearTimeout(this._errorTimer),this._errorTimer=window.setTimeout(()=>this._error="",9e3)}_change(t){this._settings={...this._settings,...t},window.clearTimeout(this._saveTimer),this._saveTimer=window.setTimeout(()=>{this.hass.callWS({type:`${w}/settings/set`,settings:this._settings}).catch(()=>{})},400)}async _write(t,e){try{await this.hass.callWS({type:`${w}/write`,entry_id:t,...e})}catch(s){this._showError(this._t("error.write",{message:this._message(s)}))}}get _selectedId(){const t=this._settings.device;return this._devices.some(e=>e.entry_id===t)?t:this._devices[0]?.entry_id??""}render(){const t=!!this.hass?.user?.is_admin,e=[["overview","nav.overview"],["device","nav.device"],["settings","nav.settings"]];return r`
      <header>
        ${this.narrow?r`<button class="menu" aria-label="menu" @click=${()=>this.dispatchEvent(new CustomEvent("hass-toggle-menu",{bubbles:!0,composed:!0}))}>☰</button>`:l}
        <span class="brand">${this._t("app.title")}</span>
        <nav>${e.map(([s,a])=>r`<button class=${this._view===s?"active":""} @click=${()=>this._view=s}>${this._t(a)}</button>`)}</nav>
      </header>
      <main
        @write=${s=>void this._write(s.detail.entry_id,s.detail.request)}
        @open-device=${s=>{this._change({device:s.detail}),this._view="device"}}
        @select-device=${s=>this._change({device:s.detail})}
        @settings-change=${s=>this._change(s.detail)}
      >
        ${this._error?r`<div class="error" role="alert">${this._error}</div>`:l}
        ${this._view==="overview"?r`<gp-overview .t=${this._t} .devices=${this._devices}></gp-overview>`:l}
        ${this._view==="device"?r`<gp-device .t=${this._t} .admin=${t} .devices=${this._devices} .selectedId=${this._selectedId}></gp-device>`:l}
        ${this._view==="settings"?r`<gp-settings .t=${this._t} .admin=${t} .settings=${this._settings} .devices=${this._devices} .selectedId=${this._selectedId}></gp-settings>`:l}
      </main>
    `}};p.styles=[A,k,$`
      :host {
        background: var(--gp-bg);
        min-height: 100vh;
      }
      header {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 12px 16px;
        border-bottom: 1px solid var(--gp-line);
        background: var(--gp-surface);
        flex-wrap: wrap;
        position: sticky;
        top: 0;
        z-index: 5;
      }
      .menu {
        background: none;
        border: none;
        cursor: pointer;
        font-size: 22px;
        padding: 0 4px;
      }
      .brand {
        font-weight: 700;
        letter-spacing: 0.04em;
      }
      nav {
        display: flex;
        gap: 6px;
        margin-left: auto;
      }
      nav button {
        background: none;
        border: 1px solid transparent;
        border-radius: 8px;
        padding: 6px 12px;
        cursor: pointer;
        color: var(--gp-fg-2);
      }
      nav button.active {
        color: var(--gp-accent);
        border-color: var(--gp-accent);
      }
      main {
        padding: 16px;
        max-width: 1200px;
        margin: 0 auto;
      }
      .error {
        background: var(--gp-magenta-wash);
        border: 1px solid var(--gp-crit);
        color: var(--gp-crit);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 12px;
      }
    `];g([d({attribute:!1})],p.prototype,"hass",2);g([d({type:Boolean})],p.prototype,"narrow",2);g([c()],p.prototype,"_devices",2);g([c()],p.prototype,"_view",2);g([c()],p.prototype,"_settings",2);g([c()],p.prototype,"_catalogue",2);g([c()],p.prototype,"_error",2);p=g([b("goalake-poe-switch-panel")],p);
