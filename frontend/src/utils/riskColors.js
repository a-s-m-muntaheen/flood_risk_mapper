export const RISK_COLORS = {
    high:   { fill: '#E24B4A', stroke: '#A32D2D', label: 'High risk' },
    medium: { fill: '#EF9F27', stroke: '#854F0B', label: 'Medium risk' },
    low:    { fill: '#1D9E75', stroke: '#085041', label: 'Low risk' },
    none:   { fill: '#888780', stroke: '#5F5E5A', label: 'Unknown' },
  }
  
  export function getRiskColor(level) {
    return RISK_COLORS[level] || RISK_COLORS.none
  }
  
  export function scoreToColor(score) {
    if (score >= 0.65) return RISK_COLORS.high
    if (score >= 0.35) return RISK_COLORS.medium
    return RISK_COLORS.low
  }
  
  export function scoreToOpacity(score) {
    return 0.3 + score * 0.5
  }