<template>
  <FileUploader
    :validateFile="validateIsImageFile"
    @success="(file) => emit('upload', file)"
  >
    <template #default="{ openFileSelector, error }">
      <div class="relative size-[42px] shrink-0">
        <AstraAvatar :name="name" :src="src" size="lg" squared />
        <Dropdown v-if="removable" :options="menu(openFileSelector)">
          <button
            type="button"
            class="absolute -bottom-1 -right-1 inline-flex size-5 items-center justify-center rounded-full bg-crm-card text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border-strong)]"
            :aria-label="__('Change image')"
          >
            <CameraIcon class="size-3" />
          </button>
        </Dropdown>
        <button
          v-else
          type="button"
          class="absolute -bottom-1 -right-1 inline-flex size-5 items-center justify-center rounded-full bg-crm-card text-crm-fg shadow-[inset_0_0_0_1px_var(--crm-border-strong)]"
          :aria-label="__('Upload image')"
          @click="openFileSelector"
        >
          <CameraIcon class="size-3" />
        </button>
        <ErrorMessage class="absolute left-0 top-full z-10 mt-1 w-40" :message="__(error)" />
      </div>
    </template>
  </FileUploader>
</template>

<script setup>
import { Dropdown, FileUploader } from 'frappe-ui'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import CameraIcon from '@/components/Icons/CameraIcon.vue'
import { validateIsImageFile } from '@/utils'

defineProps({
  name: { type: String, default: '' },
  src: { type: String, default: '' },
  removable: { type: Boolean, default: false },
})

const emit = defineEmits(['upload', 'remove'])

function menu(openFileSelector) {
  return [
    {
      label: __('Change image'),
      icon: 'lucide-upload',
      onClick: openFileSelector,
    },
    {
      label: __('Remove image'),
      icon: 'lucide-trash-2',
      onClick: () => emit('remove'),
    },
  ]
}
</script>
