// Composables
import { createRouter, createWebHistory } from 'vue-router'
const DefaultLayout = () => import('@/layouts/default/Default.vue')

const childRoutes = [
  {
    path: 'logs',
    name: 'Logs',
    component: () => import(/* webpackChunkName: "logs" */ '@/views/Logs.vue'),
  },
  {
    path: '',
    name: 'Home',
    component: () => import(/* webpackChunkName: "home" */ '@/views/Home.vue'),
  },
]

const routes = [
  {
    path: '/dist',
    component: DefaultLayout,
    children: childRoutes,
  },
  {
    path: '/BlueOS-Extensions-Repository',
    component: DefaultLayout,
    children: childRoutes,
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
})

export default router
