package com.cyberguard

import android.content.Context
import org.json.JSONObject
import java.util.regex.Pattern

/**
 * SMS Fraud Detection Engine
 * Works offline using local scam pattern database
 */
class SMSChecker(context: Context) {
    private val database: JSONObject
    
    init {
        // Load from local assets (works offline)
        val inputStream = context.assets.open("ussd_database.json")
        val jsonString = inputStream.bufferedReader().use { it.readText() }
        database = JSONObject(jsonString)
    }
    
    fun checkSMS(message: String): SecurityResult {
        if (message.isBlank()) {
            return SecurityResult(false, 0, "❌ Empty message", "gray")
        }
        
        val normalized = message.lowercase()
        
        // High-confidence scam indicators
        val highRiskPatterns = listOf(
            "won.*prize", "win.*lottery", "congratulations.*won", 
            "claim.*prize", "free.*gift", "urgent.*account",
            "bvn.*required", "password.*reset", "pin.*verification",
            "account.*suspended", "verification.*required"
        )
        
        // Medium-risk patterns
        val mediumRiskPatterns = listOf(
            "million", "cash.*award", "immediately", "click.*link",
            "call.*now", "limited.*time", "exclusive.*offer"
        )
        
        var score = 0
        val reasons = mutableListOf<String>()
        
        // Check high-risk patterns
        highRiskPatterns.forEach { pattern ->
            if (Pattern.compile(pattern, Pattern.CASE_INSENSITIVE).matcher(normalized).find()) {
                score += 8
                reasons.add("High-risk pattern: '$pattern'")
            }
        }
        
        // Check medium-risk patterns
        mediumRiskPatterns.forEach { pattern ->
            if (Pattern.compile(pattern, Pattern.CASE_INSENSITIVE).matcher(normalized).find()) {
                score += 4
                reasons.add("Medium-risk pattern: '$pattern'")
            }
        }
        
        // Check individual scam keywords from database
        val scamKeywords = database.getJSONArray("scam_keywords")
        for (i in 0 until scamKeywords.length()) {
            val keyword = scamKeywords.getString(i)
            if (normalized.contains(keyword)) {
                score += 3
                reasons.add("Scam keyword: '$keyword'")
            }
        }
        
        // Check for suspicious URLs
        if (containsSuspiciousUrl(normalized)) {
            score += 6
            reasons.add("Suspicious URL detected")
        }
        
        // Check for phone number requests
        if (containsPhoneRequest(normalized)) {
            score += 5
            reasons.add("Requests phone number")
        }
        
        // Check for money/amount mentions
        if (containsMoneyMention(normalized)) {
            score += 3
            reasons.add("Mentions money/amount")
        }
        
        // Determine result
        return when {
            score >= 15 -> SecurityResult(false, 90, "🚨 High-risk scam SMS detected!\n${reasons.joinToString(", ")}", "red")
            score >= 10 -> SecurityResult(false, 75, "⚠️ Suspicious SMS - be cautious\n${reasons.joinToString(", ")}", "orange")
            score >= 5 -> SecurityResult(false, 60, "⚠️ Potentially risky SMS\n${reasons.joinToString(", ")}", "orange")
            else -> SecurityResult(true, 95, "✅ Likely legitimate SMS", "green")
        }
    }
    
    private fun containsSuspiciousUrl(text: String): Boolean {
        val urlPatterns = listOf(
            "http://", "https://", "www\\.",
            "bit\\.ly", "tinyurl", "shorturl", "click.*here"
        )
        return urlPatterns.any { Pattern.compile(it, Pattern.CASE_INSENSITIVE).matcher(text).find() }
    }
    
    private fun containsPhoneRequest(text: String): Boolean {
        val phonePatterns = listOf(
            "call.*\\d", "phone.*number", "contact.*us",
            "dial.*\\d", "ring.*\\d", "send.*number"
        )
        return phonePatterns.any { Pattern.compile(it, Pattern.CASE_INSENSITIVE).matcher(text).find() }
    }
    
    private fun containsMoneyMention(text: String): Boolean {
        val moneyPatterns = listOf(
            "\\$\\d", "\\d+\\s*(dollar|naira|usd)", "million", "cash", "money"
        )
        return moneyPatterns.any { Pattern.compile(it, Pattern.CASE_INSENSITIVE).matcher(text).find() }
    }
    
    /**
     * Quick scan for common scam patterns (faster for real-time checking)
     */
    fun quickScan(message: String): Boolean {
        val quickScamIndicators = listOf(
            "won", "prize", "lottery", "congratulations", "claim",
            "free.*gift", "urgent", "bvn", "password", "pin"
        )
        val normalized = message.lowercase()
        return quickScamIndicators.any { Pattern.compile(it, Pattern.CASE_INSENSITIVE).matcher(normalized).find() }
    }
}
