package dev.duckzin.hidenick;

import me.neznamy.tab.api.TabPlayer;
import me.neznamy.tab.api.nametag.NameTagManager;

/** Uses only TAB's nametag API. No tab-list, prefix, suffix, profile, chat or sorting setters. */
final class NametagLease implements AutoCloseable {
    final NameTagManager manager;
    final TabPlayer player;
    private final boolean originallyHidden;
    private boolean closed;

    NametagLease(NameTagManager manager, TabPlayer player) {
        this.manager = manager;
        this.player = player;
        originallyHidden = manager.hasHiddenNameTag(player);
        enforce();
    }

    void enforce() {
        if (!closed && !manager.hasHiddenNameTag(player)) manager.hideNameTag(player);
    }

    @Override public void close() {
        if (closed) return;
        closed = true;
        if (!originallyHidden && player.isLoaded()) manager.showNameTag(player);
    }
}
