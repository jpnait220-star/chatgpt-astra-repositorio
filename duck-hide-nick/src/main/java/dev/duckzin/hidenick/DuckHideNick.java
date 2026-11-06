package dev.duckzin.hidenick;

import java.util.*;
import me.neznamy.tab.api.TabAPI;
import net.luckperms.api.LuckPerms;
import org.bukkit.*;
import org.bukkit.command.*;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.player.*;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.potion.PotionEffectType;

public final class DuckHideNick extends JavaPlugin implements Listener {
    private final Set<UUID> hidden = new HashSet<>();
    private final Map<UUID, Label> labels = new HashMap<>();
    private HiddenStore store;
    private LuckPerms luckPerms;
    private ColorPolicy colors;
    private int ticks;
    private boolean persistenceHealthy = true;
    private static final class Label {
        final TextDisplay display;
        final NametagLease lease;
        final Set<UUID> viewers = new HashSet<>();
        Label(TextDisplay display, NametagLease lease) { this.display = display; this.lease = lease; }
    }

    @Override public void onEnable() {
        saveDefaultConfig();
        luckPerms = getServer().getServicesManager().load(LuckPerms.class);
        if (luckPerms == null) { getLogger().severe("LuckPerms indisponivel."); getServer().getPluginManager().disablePlugin(this); return; }
        store = new HiddenStore(getDataFolder().toPath().resolve("players.yml"));
        try { if (getConfig().getBoolean("salvar-estado", true)) hidden.addAll(store.load()); }
        catch (Exception error) { persistenceHealthy = false; getLogger().log(java.util.logging.Level.SEVERE, "Nao foi possivel ler players.yml; arquivo preservado e salvamento desativado nesta sessao.", error); }
        loadColors();
        getServer().getPluginManager().registerEvents(this, this);
        getServer().getScheduler().runTaskTimer(this, this::tick, 1, 1);
    }
    @Override public void onDisable() {
        for (var id : new ArrayList<>(labels.keySet())) removeLabel(id);
        saveState();
    }
    private void loadColors() {
        var rules = new HashMap<String, ColorPolicy.Rule>();
        var section = getConfig().getConfigurationSection("cores.cargos");
        if (section != null) for (var group : section.getKeys(false)) {
            var entry = section.getConfigurationSection(group);
            if (entry != null) rules.put(group, new ColorPolicy.Rule(entry.getString("cor", "&7"), entry.contains("prioridade") ? entry.getInt("prioridade") : null));
        }
        colors = new ColorPolicy(rules, getConfig().getString("cores.padrao", "&7"), getConfig().getBoolean("cores.usar-cor-do-prefixo-luckperms", true));
    }
    private String color(Player player) {
        var user = luckPerms.getUserManager().getUser(player.getUniqueId());
        if (user == null) return colors.resolve(List.of(), null);
        var query = luckPerms.getContextManager().getQueryOptions(user).orElse(luckPerms.getContextManager().getStaticQueryOptions());
        var groups = user.getInheritedGroups(query).stream().map(g -> new ColorPolicy.Group(g.getName(), g.getWeight().orElse(0), g.getName().equalsIgnoreCase(user.getPrimaryGroup()))).toList();
        return colors.resolve(groups, user.getCachedData().getMetaData(query).getPrefix());
    }
    private String permission() { return getConfig().getString("permissao", "escondernick.usar"); }
    private void message(CommandSender sender, String key) { sender.sendMessage(ColorCodes.message(getConfig().getString("mensagens." + key, key))); }
    private void saveState() {
        if (store == null || !persistenceHealthy || !getConfig().getBoolean("salvar-estado", true)) return;
        try { store.save(hidden); }
        catch (Exception error) { getLogger().log(java.util.logging.Level.SEVERE, "Erro ao salvar players.yml", error); }
    }
    @Override public boolean onCommand(CommandSender sender, Command command, String name, String[] args) {
        if (command.getName().equals("ducknick")) {
            if (!sender.hasPermission("escondernick.admin")) { message(sender, "admin-sem-permissao"); return true; }
            if (args.length != 1 || !args[0].equalsIgnoreCase("reload")) { sender.sendMessage("/ducknick reload"); return true; }
            for (var id : new ArrayList<>(labels.keySet())) removeLabel(id);
            reloadConfig(); loadColors(); message(sender, "recarregado"); return true;
        }
        if (!(sender instanceof Player player)) { message(sender, "somente-jogador"); return true; }
        var id = player.getUniqueId();
        if (command.getName().equals("mostrarnick")) {
            if (!player.hasPermission(permission()) && !hidden.contains(id)) { message(player, "sem-permissao"); return true; }
            boolean removed = hidden.remove(id); removeLabel(id); saveState();
            message(player, removed ? "mostrado" : "ja-mostrado"); return true;
        }
        if (!player.hasPermission(permission())) { message(player, "sem-permissao"); return true; }
        if (player.isDead()) { message(player, "aguarde-renascer"); return true; }
        var api = TabAPI.getInstance();
        if (api.getNameTagManager() == null) { message(player, "tab-desativado"); return true; }
        var tabPlayer = api.getPlayer(id);
        if (tabPlayer == null || !tabPlayer.isLoaded()) { message(player, "carregando"); return true; }
        if (!hidden.add(id)) { message(player, "ja-escondido"); return true; }
        sync(player, true); saveState(); message(player, "escondido"); return true;
    }
    private void removeLabel(UUID id) {
        var label = labels.remove(id);
        if (label == null) return;
        label.display.remove();
        try { label.lease.close(); } catch (RuntimeException ignored) { /* TAB may be unloading. */ }
    }
    private void tick() {
        boolean refresh = ++ticks % 20 == 0;
        boolean changed = false;
        for (var id : new ArrayList<>(hidden)) {
            var player = getServer().getPlayer(id);
            if (player == null || !player.isOnline() || player.isDead()) { removeLabel(id); continue; }
            if (refresh && !player.hasPermission(permission())) { hidden.remove(id); removeLabel(id); changed = true; continue; }
            sync(player, refresh);
        }
        if (changed) saveState();
    }
    private void sync(Player player, boolean refresh) {
        var id = player.getUniqueId();
        var manager = TabAPI.getInstance().getNameTagManager();
        var tabPlayer = TabAPI.getInstance().getPlayer(id);
        var label = labels.get(id);
        if (manager == null || tabPlayer == null || !tabPlayer.isLoaded()) { removeLabel(id); return; }
        if (label != null && (label.lease.manager != manager || label.lease.player != tabPlayer || !label.display.isValid() || label.display.getWorld() != player.getWorld())) {
            removeLabel(id); label = null;
        }
        var position = player.getEyeLocation().add(0, Math.clamp(getConfig().getDouble("etiqueta.altura-acima-dos-olhos", .45), 0, 2), 0);
        position.setYaw(0); position.setPitch(0);
        if (label == null) {
            var display = player.getWorld().spawn(position, TextDisplay.class, d -> {
                d.setVisibleByDefault(false); d.setPersistent(false); d.setGravity(false); d.setInvulnerable(true);
                d.setBillboard(Display.Billboard.CENTER); d.setTeleportDuration(1); d.setShadowed(false);
                d.setDefaultBackground(getConfig().getBoolean("etiqueta.fundo", true));
                if (!getConfig().getBoolean("etiqueta.fundo", true)) d.setBackgroundColor(Color.fromARGB(0));
                d.setAlignment(TextDisplay.TextAlignment.CENTER); d.setLineWidth(300);
                d.setViewRange((float)(Math.clamp(getConfig().getDouble("etiqueta.distancia-maxima",64),8,128)/64));
                d.setText(ColorCodes.label(color(player)));
            });
            label = new Label(display, new NametagLease(manager, tabPlayer)); labels.put(id, label);
        }
        if (refresh) { label.lease.enforce(); label.display.setText(ColorCodes.label(color(player))); }
        if (label.display.getLocation().distanceSquared(position) > .000001) label.display.teleport(position);
        label.display.setSeeThrough(!player.isSneaking() && getConfig().getBoolean("etiqueta.ver-atraves-de-blocos", true));
        double range = Math.clamp(getConfig().getDouble("etiqueta.distancia-maxima",64),8,128);
        if (player.isSneaking()) range = Math.min(range,32);
        boolean invisible = getConfig().getBoolean("etiqueta.respeitar-invisibilidade",true) && (player.isInvisible() || player.hasPotionEffect(PotionEffectType.INVISIBILITY));
        for (var viewer : getServer().getOnlinePlayers()) {
            boolean visible = !invisible && !viewer.equals(player) && viewer.canSee(player) && viewer.getWorld() == player.getWorld() && viewer.getLocation().distanceSquared(position) <= range*range;
            if (visible && label.viewers.add(viewer.getUniqueId())) viewer.showEntity(this,label.display);
            else if (!visible && label.viewers.remove(viewer.getUniqueId())) viewer.hideEntity(this,label.display);
        }
    }
    @EventHandler public void quit(PlayerQuitEvent event) {
        removeLabel(event.getPlayer().getUniqueId());
        for (var label : labels.values()) label.viewers.remove(event.getPlayer().getUniqueId());
    }
    @Override public List<String> onTabComplete(CommandSender sender, Command command, String alias, String[] args) {
        return command.getName().equals("ducknick") && sender.hasPermission("escondernick.admin") && args.length == 1 && "reload".startsWith(args[0].toLowerCase(Locale.ROOT)) ? List.of("reload") : List.of();
    }
}
