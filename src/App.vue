<template>
  <div class="video-bg-container">
    <video autoplay loop muted playsinline class="global-video">
      <!-- High tech network nodes -->
      <source src="https://assets.mixkit.co/videos/preview/mixkit-connection-of-network-nodes-in-space-4198-large.mp4" type="video/mp4" />
      <source src="https://assets.codepen.io/3364143/7btrrd.mp4" type="video/mp4" />
    </video>
    <div class="video-overlay"></div>
  </div>
  <router-view />
</template>

<script setup>
//
</script>

<style>
.video-bg-container {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: -999;
  overflow: hidden;
  background-color: #03050a; /* Fallback */
}

.global-video {
  width: 100vw;
  height: 100vh;
  object-fit: cover;
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
}

.video-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(135deg, rgba(3, 5, 10, 0.75) 0%, rgba(6, 11, 24, 0.45) 100%);
}
</style>
