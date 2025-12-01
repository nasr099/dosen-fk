import api from './client'

export async function presignUpload(filename, contentType) {
  const { data } = await api.post('/files/presign', {
    filename,
    content_type: contentType || 'application/octet-stream'
  })
  return data // { upload_url, public_url, key }
}
