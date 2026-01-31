class DraftManager {
    constructor(userId = 1) {
        this.userId = userId;
    }

    getDraftKey() {
        const uid = this.userId || 0;
        return `capabilityWorksheetDraft:v1:user:${uid}`;
    }

    hasDraft() {
        try {
            return !!localStorage.getItem(this.getDraftKey());
        } catch (_) {
            return false;
        }
    }

    persistDraft(activeCapabilities, activeControls) {
        try {
            const data = {
                activeCapabilityIds: Array.from(activeCapabilities || []),
                activeControlIds: Array.from(activeControls || []),
                updatedAt: new Date().toISOString()
            };
            localStorage.setItem(this.getDraftKey(), JSON.stringify(data));
            return true;
        } catch (e) {
            console.warn('Error persisting draft:', e);
            return false;
        }
    }

    restoreDraft() {
        try {
            const raw = localStorage.getItem(this.getDraftKey());
            if (!raw) {
                return null;
            }
            const data = JSON.parse(raw);
            return {
                activeCapabilityIds: (data && data.activeCapabilityIds) || [],
                activeControlIds: (data && data.activeControlIds) || []
            };
        } catch (e) {
            console.warn('Error restoring draft:', e);
            return null;
        }
    }

    clearDraft() {
        try {
            localStorage.removeItem(this.getDraftKey());
        } catch (_) {
            // Ignore errors
        }
    }
}

