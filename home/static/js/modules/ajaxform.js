CNVS.AjaxForm = function() {
	var __core = SEMICOLON.Core;
	var __modules = SEMICOLON.Modules;

	console.log(__core)

	return {
		init: function(selector) {
			if( __core.getSelector(selector, false, false).length < 1 ){
				return true;
			}

			__core.loadJS({ file: 'plugins.form.js', id: 'canvas-form-js', jsFolder: true });

			__core.isFuncTrue( function() {
				return typeof jQuery !== 'undefined' && jQuery().validate && jQuery().ajaxSubmit;
			}).then( function(cond) {
				if( !cond ) {
					return false;
				}

				__core.initFunction({ class: 'has-plugin-form', event: 'pluginFormReady' });

				selector = __core.getSelector( selector );
				if( selector.length < 1 ){
					return true;
				}

				selector.each( function(){
					var element = jQuery(this),
						$body = jQuery('body'),
						elForm = element.find('form'), //whole form element
						elFormId = elForm.attr('id'), //block-contactform
						elAlert = element.attr('data-alert-type'), //same as elForm
						elLoader = element.attr('data-loader'), //undefined
						elResult = element.find('.form-result'),
						elRedirect = element.attr('data-redirect'), //undefined
						defaultBtn, alertType;

						// console.log(defaultBtn)

					if( !elAlert ) {
						elAlert = 'notify';
					}

					if( elFormId ) {
						$body.addClass( elFormId + '-ready' );
					}

					element.find('form').validate({
						errorPlacement: function(error, elementItem) {
							if( elementItem.parents('.form-group').length > 0 ) {
								error.appendTo( elementItem.parents('.form-group') );
							} else {
								error.insertAfter( elementItem );
							}
						},
						focusCleanup: true,

						submitHandler: function(form) {
							if( element.hasClass( 'custom-submit' ) ) {
								jQuery(form).submit();
								return true;
							}

							elResult.hide();

							if( elLoader == 'button' ) {
								defaultBtn = jQuery(form).find('button');
								defaultBtnText = defaultBtn.html();

								defaultBtn.html('<i class="bi-arrow-repeat icon-spin m-0"></i>');
							} else {
								jQuery(form).find('.form-process').fadeIn();
							}

							if( elFormId ) {
								$body.removeClass( elFormId + '-ready ' + elFormId + '-complete ' + elFormId + '-success ' + elFormId + '-error' ).addClass( elFormId + '-processing' );
							}



							jQuery(form).ajaxSubmit({

								// Target the notification
								target: elResult,
								dataType: 'json',
								success: function(data) {
									// Undefined
									if( elLoader == 'button' ) {
										defaultBtn.html( defaultBtnText );
									} else {
										// so this loads
										jQuery(form).find('.form-process').fadeOut();
									}

									// This doesn't load
									if( data.alert != 'error' && elRedirect ){
										window.location.replace( elRedirect );
										return true;
									}

									// None of this doesn't load
									if( elAlert == 'inline' ) {
										if( data.alert == 'error' ) {
											alertType = 'alert-danger';
										} else {
											alertType = 'alert-success';
										}
										elResult.removeClass( 'alert-danger alert-success' ).addClass( 'alert ' + alertType ).html( data.message ).slideDown( 400 );


									// This loads and probably sends the notification
									} else if( elAlert == 'notify' ) {
									// Modify notification if it's a report form
										if(data.report_success){
											data.message = 'Thanks for reporting this result. We will contact you soon about it.'
										}
										elResult.attr( 'data-notify-type', data.alert ).attr( 'data-notify-msg', data.message ).html('');
										__modules.notifications(elResult);
									}





									

									// If not an error
									if( data.alert != 'error' ) {
										

										jQuery(form).resetForm();
										jQuery(form).find('.btn-group > .btn').removeClass('active');


										jQuery(form).find('.input-select2,select[data-selectsplitter-firstselect-selector]').change();

										jQuery(form).trigger( 'formSubmitSuccess', data );
										$body.removeClass( elFormId + '-error' ).addClass( elFormId + '-success' );

									} else {
										jQuery(form).trigger( 'formSubmitError', data );
										$body.removeClass( elFormId + '-success' ).addClass( elFormId + '-error' );
									}

									if( elFormId ) {
										$body.removeClass( elFormId + '-processing' ).addClass( elFormId + '-complete' );
									}

									if( jQuery(form).find('.g-recaptcha').children('div').length > 0 ) {
										grecaptcha.reset();
									}
								}
							});
						}
					});

				});
			});
		}
	};
}();
