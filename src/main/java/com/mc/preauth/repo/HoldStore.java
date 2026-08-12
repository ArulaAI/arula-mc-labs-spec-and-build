package com.mc.preauth.repo;

import com.mc.preauth.domain.Hold;
import org.springframework.stereotype.Component;

import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.UnaryOperator;

/**
 * In-memory hold store. Concurrency-safe for single-hold create/read/update via
 * {@link ConcurrentHashMap#compute}, which is atomic per key.
 *
 * This scaffold intentionally stops at "safe to read and replace a single Hold snapshot."
 * It does NOT yet track idempotency keys for capture requests — that invariant (a retried
 * CaptureRequest.requestId must never apply twice) is part of what capture() must build,
 * per specs/NON_NEGOTIABLES.md.
 */
@Component
public class HoldStore {

    private final ConcurrentHashMap<String, Hold> holds = new ConcurrentHashMap<>();

    public void save(Hold hold) {
        holds.put(hold.holdId(), hold);
    }

    public Optional<Hold> find(String holdId) {
        return Optional.ofNullable(holds.get(holdId));
    }

    /**
     * Atomically replace the hold for holdId using the given transition function.
     * The function receives the current snapshot and returns the next one; it must
     * not have side effects beyond computing the new Hold, since compute() may be
     * invoked more than once under contention.
     */
    public Optional<Hold> update(String holdId, UnaryOperator<Hold> transition) {
        Hold updated = holds.compute(holdId, (id, current) ->
                current == null ? null : transition.apply(current));
        return Optional.ofNullable(updated);
    }
}
