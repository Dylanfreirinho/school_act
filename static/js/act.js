console.log('act.js is geladen!')

$(document).ready(function () {

    let studentNumber = $('#studentNumber').val()
    let statementCount = 1;
    function getNextStatement() {
        $.ajax({
            url: '/api/student/' + studentNumber + '/statement',
            method: 'GET',
            success: function (data) {
                if (data.action_type) {
                    $('#statement-container').html('<h3>Bedankt voor het invullen van de vragenlijst</h3><p>Uw type is ' + data.action_type + '</p>')
                } else {
                displayStatement(data);
                }
            },
            error: function (xhr, status, error, data) {
                console.error('Error getting next statement: ' + error);
            }
        });
    }


    function displayStatement(statementData) {
        if (statementCount > 20) {
            $('#statement-container').html('<h3>Bedankt voor het invullen van de vragenlijst!</h3>');
            return;
        }

        $('#statement-container').html('');
        $('#statement-container').append('<h3>' + statementData.statement_number + '</h3>');
        $.each(statementData.statement_choices, function (index, choice) {
            $('#statement-container').append('<button class="choice-btn" data-statement="'+ statementData.statement_number + '" data-choice="' + choice.choice_number + '">'+ choice.choice_text + '</button>');
        });
        statementCount++;
    }

    function SaveAndLoadNextStatement(statementNumber, choiceNumber) {
        $.ajax({
            url: '/api/student/' + studentNumber +'/statement/' + statementNumber + '/' + choiceNumber,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({'statement_choice': choiceNumber }),
            success: function (data) {
                 if (data.action_type) {
                    $('#statement-container').html('<h3>Bedankt voor het invullen van de vragenlijst</h3><p>Uw type is ' + data.action_type + '</p>')
                } else {
                getNextStatement();
                }
            },
            error: function (xhr, status, error, data) {
                console.error('Error saving choice: ' + error);
            }
        });
    }

    $(document).on('click', '.choice-btn', function () {
        let choiceNumber = $(this).data('choice');
        let statementNumber = $(this).data('statement');
        SaveAndLoadNextStatement(statementNumber, choiceNumber);
    });

    getNextStatement();

});