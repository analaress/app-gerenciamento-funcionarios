import { createBrowserRouter } from "react-router";
import { Layout } from "./components/Layout";
import { Dashboard } from "./components/Dashboard";
import { Colaboradores } from "./components/Colaboradores";
import { Recibos } from "./components/Recibos";
import { Rescisoes } from "./components/Rescisoes";
import { Historico } from "./components/Historico";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Layout,
    children: [
      { index: true, Component: Dashboard },
      { path: "colaboradores", Component: Colaboradores },
      { path: "recibos", Component: Recibos },
      { path: "rescisoes", Component: Rescisoes },
      { path: "historico", Component: Historico },
    ],
  },
]);
