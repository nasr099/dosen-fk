import { onMounted, onUnmounted } from 'vue';

/**
 * A composable function to detect clicks outside a given element.
 * @param {import('vue').Ref<HTMLElement | null>} el - The DOM element to monitor.
 * @param {() => void} callback - The function to call when a click outside is detected.
 */
export function useClickOutside(el, callback) {
  const listener = (e) => {
    if (!el.value || e.target === el.value || e.composedPath().includes(el.value)) {
      return;
    }
    callback();
  };

  onMounted(() => {
    document.addEventListener('click', listener);
  });

  onUnmounted(() => {
    document.removeEventListener('click', listener);
  });
}
