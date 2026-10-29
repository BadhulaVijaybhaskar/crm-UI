<template>
  <FileUploader
    :validateFile="validateIsImageFile"
    @success="(file) => emit('upload', file)"
  >
    <template #default="{ openFileSelector, error }">
      <div class="relative size-[42px] shrink-0">
        <AstraAvatar :name="name" :src="src" size="lg" squared />
        <!-- Figma .bigav has no camera affordance; keep upload via click on avatar -->
        <button
          type="button"
          class="absolute inset-0 rounded-[10px]"
          :aria-label="removable ? __('Change image') : __('Upload image')"
          @click="openFileSelector"
        />
        <ErrorMessage class="absolute left-0 top-full z-10 mt-1 w-40" :message="__(error)" />
      </div>
    </template>
  </FileUploader>
</template>

<script setup>
import { FileUploader } from 'frappe-ui'
import AstraAvatar from '@/components/astra/AstraAvatar.vue'
import { validateIsImageFile } from '@/utils'

defineProps({
  name: { type: String, default: '' },
  src: { type: String, default: '' },
  removable: { type: Boolean, default: false },
})

defineEmits(['upload', 'remove'])
</script>
