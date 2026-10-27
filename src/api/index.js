import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

http.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(new Error(error.response?.data?.error || '数据服务连接失败，请检查 Flask 服务是否启动')),
)

export const newsApi = {
  meta: () => http.get('/meta'),
  list: (params) => http.get('/news', { params }),
  detail: (id) => http.get(`/news/${id}`),
  overview: () => http.get('/stats/overview'),
  trend: () => http.get('/stats/trend'),
  categorySentiment: () => http.get('/stats/category-sentiment'),
  board: () => http.get('/stats/board'),
}

export default http
