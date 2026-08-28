import { createApp, reactive } from "vue";
import App from "./App.vue";
import "./style.css";

import router from './router';
import call from "./lib/call";
import Auth from "./lib/auth";

const app = createApp(App);
const auth = reactive(new Auth());

// Plugins
app.use(router);

// Global Properties,
// components can inject this
app.provide("$auth", auth);
app.provide("$call", call);


// Route-level auth gating (Guest/wrong-role redirects for /HR/*,
// /dashboard, /applications, /complete-profile) lives in router/index.js's
// beforeEach guard, reading window.boot rather than this Auth instance.

app.mount("#app");
