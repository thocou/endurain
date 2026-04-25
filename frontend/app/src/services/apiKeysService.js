import { fetchGetRequest, fetchPostRequest, fetchDeleteRequest } from '@/utils/serviceUtils'

export const apiKeys = {
  /**
   * Lists all API keys for the authenticated user.
   *
   * @returns {Promise} API keys list response.
   */
  listApiKeys() {
    return fetchGetRequest('api_keys')
  },

  /**
   * Creates a new API key.
   *
   * @param {Object} data - The key creation payload.
   * @param {string} data.name - User-provided label for the key.
   * @returns {Promise} Created key response including `full_key`.
   */
  createApiKey(data) {
    return fetchPostRequest('api_keys', data)
  },

  /**
   * Deletes an API key by ID.
   *
   * @param {number} keyId - The ID of the key to delete.
   * @returns {Promise} Delete response.
   */
  deleteApiKey(keyId) {
    return fetchDeleteRequest(`api_keys/${keyId}`)
  }
}
