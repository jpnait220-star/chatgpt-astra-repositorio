const input = document.querySelector('#endpoint');
const copy = document.querySelector('#copy');
const badge = document.querySelector('#badge');
const status = document.querySelector('#status');
input.value = location.origin;
copy.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(input.value); copy.textContent = 'Copiado!'; setTimeout(() => { copy.textContent = 'Copiar'; }, 2000); }
  catch { input.select(); status.textContent = 'Selecione e copie o endereço acima.'; }
});
async function check() {
  try {
    const response = await fetch('/health', { cache: 'no-store', signal: AbortSignal.timeout(4000) });
    const data = await response.json();
    if (!response.ok || data.status !== 'online') throw new Error(data.status);
    badge.textContent = 'ONLINE'; badge.className = 'badge online';
    status.textContent = 'Tudo pronto. Use o endereço abaixo no seu client.'; copy.disabled = false;
  } catch (error) {
    badge.textContent = error.message === 'unconfigured' ? 'EM CONFIGURAÇÃO' : 'INDISPONÍVEL'; badge.className = 'badge offline';
    status.textContent = error.message === 'unconfigured' ? 'O serviço ainda está sendo configurado. O endereço será liberado quando estiver pronto.' : 'Não foi possível conectar agora. Tentaremos novamente em instantes.';
    copy.disabled = true;
  }
}
check(); setInterval(check, 60000);
