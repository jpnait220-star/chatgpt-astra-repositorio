package dev.duckzin.hidenick;

import java.util.*;

final class ColorPolicy {
    record Rule(String color, Integer priority) {}
    record Group(String name, int weight, boolean primary) {}
    private final Map<String, Rule> rules;
    private final String fallback;
    private final boolean prefixFallback;
    private final boolean useRankColor;

    ColorPolicy(Map<String, Rule> rules, String fallback, boolean prefixFallback) {
        this(rules, fallback, prefixFallback, true);
    }

    ColorPolicy(Map<String, Rule> rules, String fallback, boolean prefixFallback, boolean useRankColor) {
        this.useRankColor = useRankColor;
        var copy = new HashMap<String, Rule>();
        rules.forEach((name, rule) -> copy.put(name.toLowerCase(Locale.ROOT), rule));
        this.rules = Map.copyOf(copy);
        this.fallback = ColorCodes.lastColor(fallback).orElse("§7");
        this.prefixFallback = prefixFallback;
    }

    String resolve(Collection<Group> groups, String prefix) {
        if (!useRankColor) return fallback;
        if (prefixFallback) {
            var tagColor = ColorCodes.tagColor(prefix);
            if (tagColor.isPresent()) return tagColor.get();
        }
        Group best = null;
        int bestPriority = Integer.MIN_VALUE;
        for (var group : groups) {
            var rule = rules.get(group.name().toLowerCase(Locale.ROOT));
            if (rule == null || group.name().equalsIgnoreCase("default")) continue;
            int priority = rule.priority() == null ? group.weight() : rule.priority();
            if (best == null || priority > bestPriority
                    || priority == bestPriority && group.primary() && !best.primary()
                    || priority == bestPriority && group.primary() == best.primary() && group.name().compareTo(best.name()) < 0) {
                best = group;
                bestPriority = priority;
            }
        }
        if (best != null) return ColorCodes.lastColor(rules.get(best.name().toLowerCase(Locale.ROOT)).color()).orElse(fallback);
        var defaultRule = rules.get("default");
        return defaultRule == null ? fallback : ColorCodes.lastColor(defaultRule.color()).orElse(fallback);
    }
}
