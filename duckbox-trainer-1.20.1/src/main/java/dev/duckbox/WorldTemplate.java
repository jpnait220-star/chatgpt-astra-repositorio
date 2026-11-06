package dev.duckbox;

import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Fresh copies only: never replace a world, carry player saves or follow paths out of the copy. */
public final class WorldTemplate {
  public static Path create(Path saves) throws IOException {
    try (var in = WorldTemplate.class.getResourceAsStream("/assets/duckbox/world/duckzin.zip")) {
      if (in == null) throw new IOException("Mapa de Duckzin nao encontrado no mod.");
      return extract(saves, in);
    }
  }

  public static Path extract(Path saves, InputStream source) throws IOException {
    Files.createDirectories(saves);
    Path target = null;
    for (int i = 1; i < 10000; i++) {
      Path next = saves.resolve("Mundo de Duckzin" + (i == 1 ? "" : " (" + i + ")"));
      try { Files.createDirectory(next); target = next.toAbsolutePath().normalize(); break; }
      catch (FileAlreadyExistsException exists) { /* Choose another fresh folder. */ }
    }
    if (target == null) throw new IOException("Nao foi possivel escolher uma pasta livre.");
    try {
      long bytes = 0;
      int entries = 0;
      try (var zip = new ZipInputStream(new BufferedInputStream(source))) {
        for (var e = zip.getNextEntry(); e != null; e = zip.getNextEntry()) {
          if (++entries > 4096) throw new IOException("Mapa com arquivos demais.");
          String name = e.getName().replace('\\', '/');
          Path path = target.resolve(name).normalize();
          if (name.startsWith("/") || name.contains(":") || !path.startsWith(target) || path.equals(target))
            throw new IOException("Caminho invalido no mapa.");
          if (e.isDirectory()) { Files.createDirectories(path); continue; }
          Files.createDirectories(path.getParent());
          try (var out = Files.newOutputStream(path, StandardOpenOption.CREATE_NEW)) {
            byte[] buffer = new byte[16384];
            for (int read; (read = zip.read(buffer)) != -1;) {
              if ((bytes += read) > 64L * 1024 * 1024) throw new IOException("Mapa excedeu o tamanho permitido.");
              out.write(buffer, 0, read);
            }
          }
        }
      }
      if (!Files.isRegularFile(target.resolve("level.dat"))
          || !Files.isRegularFile(target.resolve("duckbox-training.json")))
        throw new IOException("Mapa incompleto.");
      return target;
    } catch (Exception failure) {
      try (var paths = Files.walk(target)) {
        for (Path p : paths.sorted(Comparator.reverseOrder()).toList()) Files.deleteIfExists(p);
      } catch (IOException cleanup) { failure.addSuppressed(cleanup); }
      if (failure instanceof IOException io) throw io;
      throw new IOException("Falha ao copiar o mapa.", failure);
    }
  }
}
