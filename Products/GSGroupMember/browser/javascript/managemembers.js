// ABEL module for interlocks on the manage members form.
jQuery.noConflict();
ABELManageMembers = function () {
    // Private methods
    var ptnCoachChange = function () {
        var updatedWidget = jQuery(this);
        var allRelatedWidgets = jQuery(".ptnCoach :radio");
        var checkedValue = updatedWidget.attr("checked");

        if (checkedValue == true) {
            // If we select a Ptn Coach button, deselect all others
            for ( i=0 ; i < allRelatedWidgets.length ; i=i+1 ) {
                jQuery(allRelatedWidgets[i]).attr("checked", false);
            }
            // Then re-select the one that changed
            updatedWidget.attr("checked", true);
        }
    }
    
    var removeMemberChange = function () {
        var updatedWidget = jQuery(this);
        var memberId = updatedWidget.attr('id').split('-')[0].split('.')[1];
        var allRelatedWidgets = jQuery("#" + memberId + "-actions input");
        var checkedValue = updatedWidget.attr("checked");

        if (checkedValue == true) {
            // If we select the remove button, deselect and 
            // disable all other options for this member
            for ( i=0 ; i < allRelatedWidgets.length ; i=i+1 ) {
                jQuery(allRelatedWidgets[i]).attr("checked", false).attr("disabled", "disabled");
            }
            // Then re-select and re-enable the one that changed
            updatedWidget.removeAttr("disabled").attr("checked", true);
        } else {
            // If we deselect the remove button, re-enable all other options for this member
            for ( i=0 ; i < allRelatedWidgets.length ; i=i+1 ) {
                jQuery(allRelatedWidgets[i]).removeAttr("disabled");
            }
        }
    }
    
    var moderationChange = function () {
        var updatedWidget = jQuery(this);
        var memberId = updatedWidget.attr('id').split('-')[0].split('.')[1];
        var moderationAction = updatedWidget.attr('id').split('-')[1];
        var checkedValue = updatedWidget.attr("checked");
        var allRelatedWidgets = null;
        
        if (moderationAction == "moderatorAdd") {
            allRelatedWidgets = jQuery("#form\\." + memberId + "-moderatedAdd");
        } else {
            allRelatedWidgets = jQuery("#form\\." + memberId + "-moderatorAdd");
        }

        if (checkedValue == true) {
            // If we select the one Moderation checkbox, deselect and 
            // disable the other for this member
            for ( i=0 ; i < allRelatedWidgets.length ; i=i+1 ) {
                jQuery(allRelatedWidgets[i]).attr("checked", false).attr("disabled", "disabled");
            }
            // Then re-select and re-enable the one that changed
            updatedWidget.removeAttr("disabled").attr("checked", true);
        } else {
            // If we deselect the Moderation checkbox, re-enable the other option
            for ( i=0 ; i < allRelatedWidgets.length ; i=i+1 ) {
                jQuery(allRelatedWidgets[i]).removeAttr("disabled");
            }
        }
    }

    // Public methods and properties
    return {
        init: function () {
            jQuery(".ptnCoach :radio").change(ptnCoachChange);
            jQuery(".remove :checkbox").change(removeMemberChange);
            jQuery(".moderatorAdd :checkbox").change(moderationChange);
            jQuery(".moderatedAdd :checkbox").change(moderationChange);
        }
    };
}(); // ABELManageMembers

