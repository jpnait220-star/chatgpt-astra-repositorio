package dev.duckzin.hidenick;

import java.io.IOException;
import java.nio.file.*;
import java.util.*;
import org.bukkit.configuration.file.YamlConfiguration;

final class HiddenStore {
    private final Path path;
    HiddenStore(Path path) { this.path = path; }

    Set<UUID> load() throws IOException, org.bukkit.configuration.InvalidConfigurationException {
        if (!Files.exists(path)) return new HashSet<>();
        var config = new YamlConfiguration();
        config.load(path.toFile());
        var result = new HashSet<UUID>();
        for (String value : config.getStringList("ocultos")) {
            try { result.add(UUID.fromString(value)); }
            catch (IllegalArgumentException ignored) { /* Ignore a malformed entry, never a valid player's preference. */ }
        }
        return result;
    }

    void save(Collection<UUID> hidden) throws IOException {
        Files.createDirectories(path.getParent());
        var config = new YamlConfiguration();
        config.set("ocultos", hidden.stream().map(UUID::toString).sorted().toList());
        Path temp = Files.createTempFile(path.getParent(), "players-", ".tmp");
        try {
            Files.writeString(temp, config.saveToString());
            try { Files.move(temp, path, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE); }
            catch (AtomicMoveNotSupportedException ignored) { Files.move(temp, path, StandardCopyOption.REPLACE_EXISTING); }
        } finally { Files.deleteIfExists(temp); }
    }
}
