// Centralized WhatsApp config and helper
// Update the number here only (no +, country code first)
export const WHATS_NUMBER = '6289681315028'

// Build a wa.me link with a prefilled message
export function buildWaLink(message = 'Halo Admin, saya ingin upgrade akun premium.') {
  const text = typeof message === 'string' && message.trim() ? message : 'Halo Admin'
  return `https://wa.me/${WHATS_NUMBER}?text=${encodeURIComponent(text)}`
}
