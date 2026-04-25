<template>
  <div class="col">
    <div class="bg-body-tertiary rounded p-3 shadow-sm">
      <h4>{{ $t('settingsApiKeysZone.title') }}</h4>
      <p class="text-body-secondary">{{ $t('settingsApiKeysZone.description') }}</p>

      <!-- Create API Key Form -->
      <form @submit.prevent="submitCreateApiKey" class="mb-3">
        <div class="input-group">
          <input
            type="text"
            class="form-control"
            :placeholder="$t('settingsApiKeysZone.namePlaceholder')"
            v-model="newKeyName"
            maxlength="100"
            required
          />
          <button
            type="submit"
            class="btn btn-primary"
            :disabled="isCreating || !newKeyName.trim()"
          >
            <font-awesome-icon :icon="['fas', 'plus']" />
            <span class="ms-1">{{ $t('settingsApiKeysZone.createButton') }}</span>
          </button>
        </div>
      </form>

      <!-- Newly Created Key Alert -->
      <div v-if="createdKey" class="alert alert-warning alert-dismissible fade show" role="alert">
        <strong>{{ $t('settingsApiKeysZone.newKeyWarning') }}</strong>
        <div class="input-group mt-2">
          <input type="text" class="form-control font-monospace" :value="createdKey" readonly />
          <button class="btn btn-outline-secondary" type="button" @click="copyToClipboard">
            <font-awesome-icon :icon="['fas', 'copy']" />
          </button>
        </div>
        <button
          type="button"
          class="btn-close"
          @click="createdKey = ''"
          :aria-label="$t('settingsApiKeysZone.closeAlert')"
        ></button>
      </div>

      <!-- Loading -->
      <LoadingComponent v-if="isLoading" />

      <!-- API Keys Table -->
      <div v-else-if="apiKeysList.length > 0" class="table-responsive">
        <table class="table table-hover align-middle mb-0">
          <thead>
            <tr>
              <th>{{ $t('settingsApiKeysZone.columnName') }}</th>
              <th>{{ $t('settingsApiKeysZone.columnKeyPrefix') }}</th>
              <th>{{ $t('settingsApiKeysZone.columnCreated') }}</th>
              <th>{{ $t('settingsApiKeysZone.columnLastUsed') }}</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="key in apiKeysList" :key="key.id">
              <td>{{ key.name }}</td>
              <td>
                <code>{{ key.key_prefix }}****</code>
              </td>
              <td>{{ formatDate(key.created_at) }}</td>
              <td>
                {{
                  key.last_used_at ? formatDate(key.last_used_at) : $t('settingsApiKeysZone.never')
                }}
              </td>
              <td class="text-end">
                <button class="btn btn-sm btn-outline-danger" @click="deleteKey(key.id)">
                  <font-awesome-icon :icon="['fas', 'trash']" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- No Keys -->
      <p v-else class="text-body-secondary mb-0">
        {{ $t('settingsApiKeysZone.noKeys') }}
      </p>

      <!-- MCP Connection Info -->
      <hr />
      <h5>{{ $t('settingsApiKeysZone.mcpConnectionTitle') }}</h5>
      <p class="text-body-secondary">{{ $t('settingsApiKeysZone.mcpConnectionDescription') }}</p>
      <div class="bg-body rounded p-3 font-monospace small">
        <div><strong>URL:</strong> {{ mcpUrl }}</div>
        <div>
          <strong>Header:</strong> Authorization: Bearer &lt;{{
            $t('settingsApiKeysZone.yourApiKey')
          }}&gt;
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { push } from 'notivue'
import { apiKeys } from '@/services/apiKeysService'
import LoadingComponent from '@/components/GeneralComponents/LoadingComponent.vue'

interface ApiKeyResponse {
  id: number
  name: string
  key_prefix: string
  created_at: string
  last_used_at: string | null
  expires_at: string | null
}

const { t } = useI18n()

const isLoading = ref(true)
const isCreating = ref(false)
const newKeyName = ref('')
const createdKey = ref('')
const apiKeysList = ref<ApiKeyResponse[]>([])

const mcpUrl = computed(() => {
  return `${window.location.origin}/mcp`
})

/**
 * Formats an ISO date string to a localized date/time string.
 *
 * @param dateStr - The ISO date string to format.
 * @returns Formatted date string.
 */
function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString()
}

/**
 * Copies the created API key to the clipboard.
 */
async function copyToClipboard(): Promise<void> {
  try {
    await navigator.clipboard.writeText(createdKey.value)
    push.success(t('settingsApiKeysZone.keyCopied'))
  } catch {
    push.error(t('settingsApiKeysZone.keyCopyFailed'))
  }
}

/**
 * Fetches all API keys for the authenticated user.
 */
async function fetchApiKeys(): Promise<void> {
  isLoading.value = true
  try {
    apiKeysList.value = await apiKeys.listApiKeys()
  } catch (error) {
    push.error(`${t('settingsApiKeysZone.errorLoadingKeys')} - ${error}`)
  } finally {
    isLoading.value = false
  }
}

/**
 * Creates a new API key and displays the full key.
 */
async function submitCreateApiKey(): Promise<void> {
  if (!newKeyName.value.trim()) return
  isCreating.value = true
  try {
    const response = await apiKeys.createApiKey({ name: newKeyName.value.trim() })
    createdKey.value = response.full_key
    newKeyName.value = ''
    await fetchApiKeys()
    push.success(t('settingsApiKeysZone.keyCreated'))
  } catch (error) {
    push.error(`${t('settingsApiKeysZone.errorCreatingKey')} - ${error}`)
  } finally {
    isCreating.value = false
  }
}

/**
 * Deletes an API key by ID.
 *
 * @param keyId - The ID of the key to delete.
 */
async function deleteKey(keyId: number): Promise<void> {
  try {
    await apiKeys.deleteApiKey(keyId)
    await fetchApiKeys()
    push.success(t('settingsApiKeysZone.keyDeleted'))
  } catch (error) {
    push.error(`${t('settingsApiKeysZone.errorDeletingKey')} - ${error}`)
  }
}

onMounted(() => {
  fetchApiKeys()
})
</script>
