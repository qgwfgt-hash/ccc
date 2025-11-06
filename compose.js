'use strict';

let composeAlert = $('#alert-compose');

var removeFile = null;

var $form = $('#form');
var $to = $('#to');
var $subject = $('#subject');
var $text = $('#text');
var $fileList = $('#file_list');
var $fileSize = $('#file_size');
var $submit = $('#submit');
var $cancel = $('#cancel');
var $fileProgress = $('#file_progress');
var $fileForm = $('#file_form');
var fileList = [];
var fileSize = 0;

var template = doT.template($('#t_file').text());

removeFile = function(button) {
	var $div = $(button).parent('div');
	var i = $fileList.children().index($div);

	$div.remove();
	fileSize -= fileList[i].size;
	fileList.splice(i, 1);

	updateFileSize();

	return false;
};

function updateFileSize() {
	$fileSize.text(fileList.length > 1 && fileSize ? fex.formatSize(fileSize) : '');
}

$('#file').change(function() {
	var files = $(this)[0].files;
	var size = 0;

	for (var i = 0; i < files.length; i++) {
		size += files[i].size;
	}

	if (fileSize + size > 50 * 1024 * 1024) {
		showAlert('attachments_too_large', composeAlert);
		$fileForm[0].reset();
		return;
	}

	for (var i = 0; i < files.length; i++) {
		fileList.push(files[i]);
		fileSize += files[i].size;
	}

	$fileList.append(template(files));
	updateFileSize();

	$fileForm[0].reset();
});

$form.submit(function() {
	var startTime = new Date().getTime();
	var progressOn = false;

	$submit.prop('disabled', true);

	var formData = new FormData();
	formData.append('email', fex.email);
	if (fex.epin) {
		formData.append('epin', fex.epin);
	}
	formData.append('to', $to.val());
	formData.append('subject', $subject.val());
	formData.append('content_type', 'text/html');
	formData.append('text', $text.html());

	for (var i = 0; i < fileList.length; i++) {
		formData.append('file', fileList[i]);
	}

	fex.ajax({
		type		: 'POST',
		url		: '/api/mails/',
		data		: formData,
		contentType	: false,
		enctype		: 'multipart/form-data',
		processData	: false,
		xhr		: function() {
			var xhr = new window.XMLHttpRequest();
			xhr.upload.addEventListener('progress', function(e) {
				if (!progressOn) {
					progressOn = new Date().getTime() - startTime > 1000;
				}
				if (progressOn && e.lengthComputable && e.total) {
					$fileProgress.width(Math.round(e.loaded * 100 / e.total) + '%');
				}
			}, false);
			return xhr;
		}
	}).done(function(j) {
		$fileProgress.width(0);
		$submit.prop('disabled', false);

		showAlert(j.err ? j.err.msg : null, composeAlert);

		if (j.result) {
			showAlert('message_successfully_sent', null, true);

			$('#modal-compose').modal('hide');

			$text.empty();
			$fileList.empty();
			$fileSize.empty();

			fileList = [];
			fileSize = 0;

			$form[0].reset();
			$fileForm[0].reset();
		}
	}).fail(function() {
		$fileProgress.width(0);
		$submit.prop('disabled', false);

		showAlert('unable_send_message', composeAlert);
	});

	return false;
});

$cancel.click(function() {
	fex.go(mail_id ? 'mail/' + mail_id : '');
});

$('#modal-compose').on('show.bs.modal', function(e) {
	var mail_id = fex.paramInt(1);

	if (mail_id) {
		var mail = fex.mail[mail_id];

		if (!mail) { return; }

		$to.val(mail.from);
		$subject.val((/^re:/i.test(mail.subject) ? '' : 'Re: ') + mail.subject);
	}
});

$('#modal-compose').on('shown.bs.modal', function(e) {
	if ($(window).width() < 1200) {
		scrollToTop();
	}

	$to.focus();
});
