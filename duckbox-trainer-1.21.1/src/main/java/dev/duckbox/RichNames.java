package dev.duckbox;

import java.util.*;
import java.util.regex.*;
import net.minecraft.text.*;
import net.minecraft.util.Formatting;

/** Static item/profile colors: Birdflop legacy hex, gradients, rainbow and style tags. */
public final class RichNames {
  private static final Pattern SPECIAL =
      Pattern.compile(
          "<(gradient:[^>]+|rainbow(?::[^>]+)?)>(.*?)</(?:gradient|rainbow)>",
          Pattern.CASE_INSENSITIVE | Pattern.DOTALL);
  private static final Style BASE = Style.EMPTY.withItalic(false);

  public static Text parse(String raw) {
    if (raw == null || raw.length() > 4096)
      throw new IllegalArgumentException("Nome muito grande (maximo4096 caracteres de codigo).");
    Text text = markup(raw, 0);
    if (text.getString().codePointCount(0, text.getString().length()) > 256)
      throw new IllegalArgumentException("Nome visivel: maximo256 caracteres.");
    return text;
  }

  private static MutableText markup(String raw, int depth) {
    if (depth > 8) throw new IllegalArgumentException("Muitas tags aninhadas.");
    var out = Text.empty();
    var matcher = SPECIAL.matcher(raw);
    int last = 0;
    while (matcher.find()) {
      out.append(legacy(raw.substring(last, matcher.start())));
      Text inner = markup(matcher.group(2), depth + 1);
      String mode = matcher.group(1);
      int[] colors = null;
      if (mode.toLowerCase(Locale.ROOT).startsWith("gradient:")) {
        String[] parts = mode.substring(9).split(":");
        if (parts.length < 2)
          throw new IllegalArgumentException("Gradiente precisa de pelo menos2 cores.");
        colors = new int[parts.length];
        for (int i = 0; i < parts.length; i++) colors[i] = color(parts[i]);
      }
      final int[] palette = colors;
      final int total =
          Math.max(1, inner.getString().codePointCount(0, inner.getString().length()) - 1);
      final int[] index = {0};
      final boolean reverse = mode.contains("!");
      inner.visit(
          (style, text) -> {
            text.codePoints()
                .forEach(
                    cp -> {
                      float fraction = (float) index[0]++ / total;
                      int rgb;
                      if (palette == null)
                        rgb =
                            java.awt.Color.HSBtoRGB(reverse ? 1 - fraction : fraction, 1, 1)
                                & 0xffffff;
                      else {
                        double step = fraction * (palette.length - 1);
                        int part = Math.min(palette.length - 2, (int) step);
                        double t = step - part;
                        int a = palette[part], b = palette[part + 1];
                        int r =
                            (int) Math.round(((a >> 16) & 255) * (1 - t) + ((b >> 16) & 255) * t);
                        int g = (int) Math.round(((a >> 8) & 255) * (1 - t) + ((b >> 8) & 255) * t);
                        int bl = (int) Math.round((a & 255) * (1 - t) + (b & 255) * t);
                        rgb = (r << 16) | (g << 8) | bl;
                      }
                      out.append(
                          Text.literal(new String(Character.toChars(cp)))
                              .setStyle(style.withColor(rgb)));
                    });
            return Optional.empty();
          },
          BASE);
      last = matcher.end();
    }
    out.append(legacy(raw.substring(last)));
    return out;
  }

  private static int color(String value) {
    String h = value.startsWith("#") ? value.substring(1) : value;
    if (!h.matches("[a-fA-F0-9]{6}"))
      throw new IllegalArgumentException("Cor RGB invalida: " + value);
    return Integer.parseInt(h, 16);
  }

  private static MutableText legacy(String raw) {
    var out = Text.empty();
    Style style = BASE;
    var stack = new ArrayDeque<Style>();
    for (int i = 0; i < raw.length(); ) {
      char ch = raw.charAt(i);
      if ((ch == '&' || ch == '§') && i + 1 < raw.length()) {
        char code = Character.toLowerCase(raw.charAt(i + 1));
        if (code == '#' && i + 8 <= raw.length()) {
          style = style.withColor(color(raw.substring(i + 2, i + 8)));
          i += 8;
          continue;
        }
        if (code == 'x' && i + 14 <= raw.length()) {
          StringBuilder hex = new StringBuilder();
          boolean valid = true;
          for (int k = 0; k < 6; k++) {
            int j = i + 2 + k * 2;
            if (raw.charAt(j) != '&' && raw.charAt(j) != '§') {
              valid = false;
              break;
            }
            hex.append(raw.charAt(j + 1));
          }
          if (valid) {
            style = style.withColor(color(hex.toString()));
            i += 14;
            continue;
          }
        }
        Formatting f = Formatting.byCode(code);
        if (f != null) {
          style =
              switch (code) {
                case 'l' -> style.withBold(true);
                case 'o' -> style.withItalic(true);
                case 'n' -> style.withUnderline(true);
                case 'm' -> style.withStrikethrough(true);
                case 'k' -> style.withObfuscated(true);
                case 'r' -> BASE;
                default -> BASE.withColor(f);
              };
          i += 2;
          continue;
        }
      }
      if (ch == '<') {
        int end = raw.indexOf('>', i);
        if (end >= 0) {
          String tag = raw.substring(i + 1, end).toLowerCase(Locale.ROOT);
          String name = tag.startsWith("/") ? tag.substring(1) : tag;
          boolean known =
              Set.of(
                          "bold",
                          "b",
                          "italic",
                          "i",
                          "underlined",
                          "u",
                          "strikethrough",
                          "st",
                          "obfuscated",
                          "obf",
                          "color",
                          "reset")
                      .contains(name)
                  || name.startsWith("#")
                  || name.startsWith("color:")
                  || Formatting.byName(name) != null;
          if (known) {
            if (tag.startsWith("/")) {
              style = stack.isEmpty() ? BASE : stack.pop();
            } else {
              stack.push(style);
              style =
                  switch (name) {
                    case "bold", "b" -> style.withBold(true);
                    case "italic", "i" -> style.withItalic(true);
                    case "underlined", "u" -> style.withUnderline(true);
                    case "strikethrough", "st" -> style.withStrikethrough(true);
                    case "obfuscated", "obf" -> style.withObfuscated(true);
                    case "reset" -> BASE;
                    case "color" -> style;
                    default ->
                        name.startsWith("#") || name.startsWith("color:")
                            ? style.withColor(
                                color(name.startsWith("color:") ? name.substring(6) : name))
                            : style.withColor(Formatting.byName(name));
                  };
            }
            i = end + 1;
            continue;
          }
        }
      }
      int cp = raw.codePointAt(i);
      out.append(Text.literal(new String(Character.toChars(cp))).setStyle(style));
      i += Character.charCount(cp);
    }
    return out;
  }
}
