/** @odoo-module **/
import {browser} from "@web/core/browser/browser";
import {registry} from "@web/core/registry";

// Define service
// export const pageRefreshService = {
//     dependencies: ["bus_service"],
//     start(env, { bus_service }) {
//         console.log("Registering bus service for page refresh");
//         // Subscribe to bus event
//         const model_name = 'mrp.workorder'
//         bus_service.subscribe("page_refresh", (payload) => {
//             console.log("Received page refresh notification", payload);
//         });
//         function reloadOnIncomingWebhooks() {

//             // Access the action service directly from env.
//             // Hard & soft refresh actions are already defined
//             // in odoo.
//             const actionService = env.services.action;

//             // Note : Change the logic according to your specific
//             // usecase.
//             // Remove the '#' character
//             const hash = window.location.hash.slice(1);
//             const urlParams = new URLSearchParams(hash);

//             if (urlParams.has('view_type') && urlParams.get('view_type') === 'form') {
//                 console.log("Executing hard reload");
//                 // Perform a hard refresh.
//                 // Invoke hard refresh client action.
//                 actionService.doAction({
//                     type: "ir.actions.client",
//                     tag: "reload",
//                 });
//             } else {
//                 console.log("Executing soft reload");
//                 // Soft refresh for other view types.
//                 // Invoke soft refresh client action.
//                 actionService.doAction({
//                     type: "ir.actions.client",
//                     tag: "soft_reload",
//                 });
//             }
//         }
//     },
// };

// // Register the service
// registry.category("services").add("pageRefresh", pageRefreshService);

// ref: https://medium.com/@krishnajithdev673/manually-triggering-a-soft-or-hard-refresh-in-odoo-from-the-backend-e5bfe2972d9f
