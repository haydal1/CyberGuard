package com.cyberguard

import android.content.Context
import org.json.JSONObject

/**
 * Core USSD security checking engine
 * Works completely offline using local database
 */
class USSDChecker(context: Context) {
    private val database: JSONObject
    
    init {
        // Load from local assets (works offline)
        val inputStream = context.assets.open("ussd_database.json")
        val jsonString = inputStream.bufferedReader().use { it.readText() }
        database = JSONObject(jsonString)
    }
    
    fun checkCode(code: String): SecurityResult {
        // 1. Normalize the code
        val normalized = normalizeUSSD(code)
        
        if (normalized.isEmpty()) {
            return SecurityResult(false, 0, "❌ Please enter a valid USSD code")
        }
        
        // 2. Check if known safe code
        val safeCodes = database.getJSONArray("safe_ussd_codes")
        for (i in 0 until safeCodes.length()) {
            if (normalized == safeCodes.getString(i)) {
                return SecurityResult.SAFE
            }
        }
        
        // 3. Check for suspicious patterns
        if (hasSuspiciousPattern(normalized)) {
            return SecurityResult.SUSPICIOUS
        }
        
        // 4. Check segment count
        if (countSegments(normalized) > 4) {
            return SecurityResult(false, 70, "⚠️ Too many segments - be cautious")
        }
        
        // 5. Check for scam keywords in dynamic parts
        if (containsScamKeywords(normalized)) {
            return SecurityResult.DANGEROUS
        }
        
        // 6. Check if it starts with known safe prefix
        if (hasSafePrefix(normalized)) {
            return SecurityResult(true, 60, "✅ Starts with known safe prefix")
        }
        
        return SecurityResult.UNKNOWN
    }
    
    private fun normalizeUSSD(code: String): String {
        return code.trim().replace(" ", "").uppercase()
    }
    
    private fun hasSuspiciousPattern(code: String): Boolean {
        val patterns = database.getJSONArray("suspicious_patterns")
        for (i in 0 until patterns.length()) {
            val pattern = patterns.getString(i)
            // Simple pattern matching for suspicious formats
            if (code.matches(Regex(pattern.replace("xxx", ".*")))) {
                return true
            }
        }
        return false
    }
    
    private fun countSegments(code: String): Int {
        return code.split("*").size - 1
    }
    
    private fun containsScamKeywords(code: String): Boolean {
        val keywords = database.getJSONArray("scam_keywords")
        for (i in 0 until keywords.length()) {
            val keyword = keywords.getString(i)
            if (code.contains(keyword, ignoreCase = true)) {
                return true
            }
        }
        return false
    }
    
    private fun hasSafePrefix(code: String): Boolean {
        val safePrefixes = database.getJSONObject("rules").getJSONArray("safe_prefixes")
        for (i in 0 until safePrefixes.length()) {
            if (code.startsWith(safePrefixes.getString(i))) {
                return true
            }
        }
        return false
    }
    
    /**
     * Get database statistics for debugging
     */
    fun getDatabaseStats(): String {
        val safeCount = database.getJSONArray("safe_ussd_codes").length()
        val scamCount = database.getJSONArray("scam_keywords").length()
        return "Database: $safeCount safe codes, $scamCount scam patterns"
    }
}
