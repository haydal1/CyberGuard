package com.cyberguard

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.provider.Telephony
import android.widget.Toast
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat

/**
 * Automatic SMS Fraud Detection Receiver
 * Monitors incoming SMS messages and alerts user about potential scams
 */
class SMSReceiver : BroadcastReceiver() {
    
    override fun onReceive(context: Context, intent: Intent) {
        // Check if the user has enabled automatic SMS detection
        val prefs = context.getSharedPreferences("cyberguard_prefs", Context.MODE_PRIVATE)
        val autoDetectionEnabled = prefs.getBoolean("auto_sms_detection", true)
        
        if (!autoDetectionEnabled) {
            return // Automatic detection is disabled by user
        }
        
        if (intent.action == Telephony.Sms.Intents.SMS_RECEIVED_ACTION) {
            val smsMessages = Telephony.Sms.Intents.getMessagesFromIntent(intent)
            
            for (sms in smsMessages) {
                val messageBody = sms.displayMessageBody
                val sender = sms.displayOriginatingAddress
                
                if (messageBody != null) {
                    // Check if the SMS is a potential scam
                    val smsChecker = SMSChecker(context)
                    val result = smsChecker.checkSMS(messageBody)
                    
                    // Only alert for high-risk scams
                    if (!result.isSafe && result.confidence >= 75) {
                        showScamAlert(context, messageBody, result.message, sender)
                    }
                }
            }
        }
    }
    
    private fun showScamAlert(
        context: Context, 
        originalMessage: String, 
        analysis: String,
        sender: String?
    ) {
        // Create notification
        val notificationId = System.currentTimeMillis().toInt()
        
        val notification = NotificationCompat.Builder(context, "cyberguard_alerts")
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle("🚨 CyberGuard: Potential Scam Detected")
            .setContentText("SMS from ${sender ?: "unknown"} may be fraudulent")
            .setStyle(NotificationCompat.BigTextStyle()
                .bigText("SMS: ${originalMessage.take(100)}...\n\nAnalysis: $analysis"))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .build()
        
        // Show notification
        with(NotificationManagerCompat.from(context)) {
            notify(notificationId, notification)
        }
        
        // Optional: Show toast message
        Toast.makeText(
            context, 
            "🚨 Potential scam SMS detected from $sender", 
            Toast.LENGTH_LONG
        ).show()
    }
}
