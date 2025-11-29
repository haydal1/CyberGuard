package com.cyberguard

/**
 * Data class representing the result of a USSD security check
 */
data class SecurityResult(
    val isSafe: Boolean,
    val confidence: Int,
    val message: String,
    val needsInternet: Boolean = false
) {
    companion object {
        val SAFE = SecurityResult(true, 95, "✅ Known safe USSD code")
        val SUSPICIOUS = SecurityResult(false, 80, "⚠️ Suspicious pattern detected")
        val DANGEROUS = SecurityResult(false, 90, "🚨 Contains scam keywords!")
        val UNKNOWN = SecurityResult(false, 50, "❓ Unknown code - use caution", true)
    }
}
