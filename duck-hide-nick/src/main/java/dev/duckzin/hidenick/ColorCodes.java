package dev.duckzin.hidenick;

import java.util.Locale;
import java.util.Optional;
import java.util.regex.Pattern;

final class ColorCodes {
    private static final Pattern COLOR = Pattern.compile("(?i)(&#[0-9a-f]{6}|#[0-9a-f]{6}|[&§]x(?:[&§][0-9a-f]){6}|[&§][0-9a-f])");
    private ColorCodes() {}

    static Optional<String> lastColor(String input) {
        if (input == null) return Optional.empty();
        var matcher = COLOR.matcher(input);
        String last = null;
        while (matcher.find()) last = normalize(matcher.group());
        return Optional.ofNullable(last);
    }

    /** Color of the tag's first letter/number, ignoring brackets and trailing resets. */
    static Optional<String> tagColor(String input) {
        if (input == null) return Optional.empty();
        String text = message(input);
        String active = null;
        for (int i = 0; i < text.length(); i++) {
            if (text.charAt(i) == '§' && i + 1 < text.length()) {
                char code = Character.toLowerCase(text.charAt(i + 1));
                if (code == 'x' && i + 14 <= text.length()) {
                    String candidate = text.substring(i, i + 14);
                    if (COLOR.matcher(candidate).matches()) { active = normalize(candidate); i += 13; continue; }
                }
                if ("0123456789abcdef".indexOf(code) >= 0) active = "§" + code;
                else if (code == 'r') active = null;
                i++;
                continue;
            }
            if (Character.isLetterOrDigit(text.charAt(i)) && active != null) return Optional.of(active);
        }
        return lastColor(input);
    }

    static String normalize(String raw) {
        String value = raw.toLowerCase(Locale.ROOT).replace('&', '§');
        if (value.startsWith("§#")) value = value.substring(1);
        if (value.startsWith("#")) {
            var result = new StringBuilder("§x");
            for (int i = 1; i < value.length(); i++) result.append('§').append(value.charAt(i));
            return result.toString();
        }
        return value;
    }

    static String message(String input) {
        if (input == null) return "";
        var hex = Pattern.compile("(?i)&#[0-9a-f]{6}").matcher(input);
        var output = new StringBuffer();
        while (hex.find()) hex.appendReplacement(output, java.util.regex.Matcher.quoteReplacement(normalize(hex.group())));
        hex.appendTail(output);
        var text = output.toString();
        var result = new StringBuilder();
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c == '&' && i + 1 < text.length() && "0123456789abcdefklmnorxABCDEFKLMNORX".indexOf(text.charAt(i + 1)) >= 0)
                result.append('§');
            else result.append(c);
        }
        return result.toString();
    }

    static String label(String color) {
        return lastColor(color).orElse("§7") + "§kXXXXXXXXX§r";
    }
}
