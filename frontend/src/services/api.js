import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const floodZoneApi = {
  getZones: () => api.get('/flood-zones/'),
  getZoneById: (id) => api.get(`/flood-zones/${id}/`),
  getRiskScore: (geometry) => api.post('/risk/score/', { geometry }),
}

export default api