import Vue from 'vue'
import VueRouter from 'vue-router'
const NewsView = () => import('../views/news.vue')
const SentimentView = () => import('../views/sentiment.vue')
const BoardView = () => import('../views/board.vue')

Vue.use(VueRouter)

export default new VueRouter({
  mode: 'hash',
  routes: [
    { path: '/', redirect: '/news' },
    { path: '/news', name: 'news', component: NewsView, meta: { title: '新闻库' } },
    { path: '/sentiment', name: 'sentiment', component: SentimentView, meta: { title: '情感洞察' } },
    { path: '/board', name: 'board', component: BoardView, meta: { title: '可视化大屏' } },
    { path: '*', redirect: '/news' },
  ],
})
