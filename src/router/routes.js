const routes = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      { path: '',         redirect: '/dashboard' },
      { path: 'dashboard',component: () => import('pages/IndexPage.vue')    },
      { path: 'tracking', component: () => import('pages/TrackingPage.vue') },
      { path: 'orders',   component: () => import('pages/OrdersPage.vue')   },
      { path: 'routes',   component: () => import('pages/RoutesPage.vue')   },
      { path: 'drivers',  component: () => import('pages/DriversPage.vue')  },
      { path: 'stock',    component: () => import('pages/StockPage.vue')    },
      { path: 'settings', component: () => import('pages/SettingsPage.vue') },
    ],
  },
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
]

export default routes
