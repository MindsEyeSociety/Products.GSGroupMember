// ABEL module for interlocks on the manage members form.
jQuery.noConflict();
ABELManageMembers = function () {
    // Private methods
    var ptnCoachChange = function () {
        var updatedWidget = jQuery(this);
        var allRelatedWidgets = jQuery(".ptnCoachAdd :radio");
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

    // Public methods and properties
    return {
        init: function () {
            jQuery(".ptnCoachAdd :radio").change(ptnCoachChange);
        }
    };
}(); // ABELManageMembers

