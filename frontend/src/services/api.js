import axios from 'axios'

function getCookie(name) {
  const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'))
  return match ? match[2] : null
}

const api = axios.create({
  baseURL:         '/api',
  withCredentials: true,
  headers:         { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  if (['post', 'put', 'patch', 'delete'].includes(config.method)) {
    const csrf = getCookie('csrftoken')
    if (csrf) config.headers['X-CSRFToken'] = csrf
  }
  return config
})

export const riskApi = {
  getZones:      (params = {}) => api.get('/risk/zones/',         { params }),
  getZoneDetail: (id)          => api.get(`/risk/zones/${id}/`),
  scoreGeometry: (geometry)    => api.post('/risk/score/',        { geometry }),
  getStats:      ()            => api.get('/risk/stats/'),
  getModelInfo:  ()            => api.get('/risk/model-info/'),
  healthCheck:   ()            => api.get('/flood-zones/health/'),
}

export default api