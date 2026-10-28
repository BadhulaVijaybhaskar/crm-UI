<template>
  <div
    v-if="matches?.length"
    class="mt-4 rounded-md border border-outline-gray-2 bg-surface-gray-2 px-3 py-2 text-sm text-ink-gray-8"
    role="status"
  >
    <p class="text-p-sm-medium text-ink-gray-9">
      {{ __('Possible duplicates found') }}
    </p>
    <p class="mt-1 text-p-sm text-ink-gray-7">
      {{
        __(
          'You can still create this record. Review these matches if this might already exist.',
        )
      }}
    </p>
    <ul class="mt-2 space-y-1">
      <li v-for="m in matches" :key="m.name">
        <button
          type="button"
          class="text-left text-p-sm text-ink-gray-9 underline-offset-2 hover:underline"
          @click="open(m)"
        >
          {{ m.title || m.name }}
          <span class="text-ink-gray-5">
            ({{ (m.matched_on || []).map(labelFor).join(', ') }})
          </span>
        </button>
      </li>
    </ul>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const props = defineProps({
  matches: { type: Array, default: () => [] },
})

const router = useRouter()

const labels = {
  email: __('Email'),
  phone: __('Phone'),
  company_domain: __('Company domain'),
}

function labelFor(key) {
  return labels[key] || key
}

function open(m) {
  const map = {
    'CRM Lead': { name: 'Lead', param: 'leadId' },
    Contact: { name: 'Contact', param: 'contactId' },
    'CRM Organization': { name: 'Organization', param: 'organizationId' },
  }
  const route = map[m.doctype]
  if (!route) return
  router.push({ name: route.name, params: { [route.param]: m.name } })
}
</script>
